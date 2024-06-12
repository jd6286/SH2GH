import sys


if __name__ == "__main__":
    print("This is not an executable script. Please run main.py.")
    sys.exit(-1)


import os
import torch
import openvino as ov
import gradio as gr
import numpy as np
import rembg

from pathlib import Path
from collections import namedtuple
from PIL import Image
from diffusers.utils import load_image 

# TripoSR 라이브러리가 없는 경우
if not Path("TripoSR").exists():
    os.system('git clone https://huggingface.co/spaces/stabilityai/TripoSR')

# TripoSR 라이브러리의 경로 추가
sys.path.append("TripoSR")
from tsr.system import TSR
from tsr.utils import remove_background, resize_foreground, to_gradio_3d_orientation

# TripoSR 모델 불러오기 
model = TSR.from_pretrained(
    "stabilityai/TripoSR",
    config_name="config.yaml",
    weight_name="model.ckpt",
)
model.renderer.set_chunk_size(131072)
model.to("cpu")

# PyTorch 모델을 openVINO IR로 변환
def convert(model: torch.nn.Module, xml_path: str, example_input):
    xml_path = Path(xml_path)
    if not xml_path.exists():
        xml_path.parent.mkdir(parents=True, exist_ok=True)
        with torch.no_grad():
            converted_model = ov.convert_model(model, example_input=example_input)
        ov.save_model(converted_model, xml_path, compress_to_fp16=False)

        # cleanup memory
        torch._C._jit_clear_class_registry()
        torch.jit._recursive.concrete_type_store = torch.jit._recursive.ConcreteTypeStore()
        torch.jit._state._clear_class_state()

# 이미지 처리 모델을 openVINO IR로 변환 
VIT_PATCH_EMBEDDINGS_OV_PATH = Path("models/vit_patch_embeddings_ir.xml")


class PatchEmbedingWrapper(torch.nn.Module):
    def __init__(self, patch_embeddings):
        super().__init__()
        self.patch_embeddings = patch_embeddings

    def forward(self, pixel_values, interpolate_pos_encoding=True):
        outputs = self.patch_embeddings(pixel_values=pixel_values, interpolate_pos_encoding=True)
        return outputs
    
example_input = {
    "pixel_values": torch.rand([1, 3, 512, 512], dtype=torch.float32),
}

convert(
    PatchEmbedingWrapper(model.image_tokenizer.model.embeddings.patch_embeddings),
    VIT_PATCH_EMBEDDINGS_OV_PATH,
    example_input,
)

VIT_ENCODER_OV_PATH = Path("models/vit_encoder_ir.xml")


class EncoderWrapper(torch.nn.Module):
    def __init__(self, encoder):
        super().__init__()
        self.encoder = encoder

    def forward(
        self,
        hidden_states=None,
        head_mask=None,
        output_attentions=False,
        output_hidden_states=False,
        return_dict=False,
    ):
        outputs = self.encoder(
            hidden_states=hidden_states,
        )

        return outputs.last_hidden_state


example_input = {
    "hidden_states": torch.rand([1, 1025, 768], dtype=torch.float32),
}

convert(
    EncoderWrapper(model.image_tokenizer.model.encoder),
    VIT_ENCODER_OV_PATH,
    example_input,
)

VIT_POOLER_OV_PATH = Path("models/vit_pooler_ir.xml")
convert(
    model.image_tokenizer.model.pooler,
    VIT_POOLER_OV_PATH,
    torch.rand([1, 1025, 768], dtype=torch.float32),
)

TOKENIZER_OV_PATH = Path("models/tokenizer_ir.xml")
convert(model.tokenizer, TOKENIZER_OV_PATH, torch.tensor(1))

example_input = {
    "hidden_states": torch.rand([1, 1024, 3072], dtype=torch.float32),
    "encoder_hidden_states": torch.rand([1, 1025, 768], dtype=torch.float32),
}

BACKBONE_OV_PATH = Path("models/backbone_ir.xml")
convert(model.backbone, BACKBONE_OV_PATH, example_input)

POST_PROCESSOR_OV_PATH = Path("models/post_processor_ir.xml")
convert(
    model.post_processor,
    POST_PROCESSOR_OV_PATH,
    torch.rand([1, 3, 1024, 32, 32], dtype=torch.float32),
)

# # OpenVINO의 코어를 가져옴
# core = ov.Core()
# device = "CPU"

# # 모델 컴파일 
# compiled_vit_patch_embeddings = core.compile_model(VIT_PATCH_EMBEDDINGS_OV_PATH, device)
# compiled_vit_model_encoder = core.compile_model(VIT_ENCODER_OV_PATH, device)
# compiled_vit_model_pooler = core.compile_model(VIT_POOLER_OV_PATH, device)

# compiled_tokenizer = core.compile_model(TOKENIZER_OV_PATH, device)
# compiled_backbone = core.compile_model(BACKBONE_OV_PATH, device)
# compiled_post_processor = core.compile_model(POST_PROCESSOR_OV_PATH, device)

class VitPatchEmdeddingsWrapper(torch.nn.Module):
    def __init__(self, vit_patch_embeddings, model):
        super().__init__()
        self.vit_patch_embeddings = vit_patch_embeddings
        self.projection = model.projection

    def forward(self, pixel_values, interpolate_pos_encoding=False):
        inputs = {
            "pixel_values": pixel_values,
        }
        outs = self.vit_patch_embeddings(inputs)[0]

        return torch.from_numpy(outs)


class VitModelEncoderWrapper(torch.nn.Module):
    def __init__(self, vit_model_encoder):
        super().__init__()
        self.vit_model_encoder = vit_model_encoder

    def forward(
        self,
        hidden_states,
        head_mask,
        output_attentions=False,
        output_hidden_states=False,
        return_dict=False,
    ):
        inputs = {
            "hidden_states": hidden_states.detach().numpy(),
        }

        outs = self.vit_model_encoder(inputs)
        outputs = namedtuple("BaseModelOutput", ("last_hidden_state", "hidden_states", "attentions"))

        return outputs(torch.from_numpy(outs[0]), None, None)


class VitModelPoolerWrapper(torch.nn.Module):
    def __init__(self, vit_model_pooler):
        super().__init__()
        self.vit_model_pooler = vit_model_pooler

    def forward(self, hidden_states):
        outs = self.vit_model_pooler(hidden_states.detach().numpy())[0]

        return torch.from_numpy(outs)


class TokenizerWrapper(torch.nn.Module):
    def __init__(self, tokenizer, model):
        super().__init__()
        self.tokenizer = tokenizer
        self.detokenize = model.detokenize

    def forward(self, batch_size):
        outs = self.tokenizer(batch_size)[0]

        return torch.from_numpy(outs)


class BackboneWrapper(torch.nn.Module):
    def __init__(self, backbone):
        super().__init__()
        self.backbone = backbone

    def forward(self, hidden_states, encoder_hidden_states):
        inputs = {
            "hidden_states": hidden_states,
            "encoder_hidden_states": encoder_hidden_states.detach().numpy(),
        }

        outs = self.backbone(inputs)[0]

        return torch.from_numpy(outs)


class PostProcessorWrapper(torch.nn.Module):
    def __init__(self, post_processor):
        super().__init__()
        self.post_processor = post_processor

    def forward(self, triplanes):
        outs = self.post_processor(triplanes)[0]

        return torch.from_numpy(outs)


# model.image_tokenizer.model.embeddings.patch_embeddings = VitPatchEmdeddingsWrapper(
#     compiled_vit_patch_embeddings,
#     model.image_tokenizer.model.embeddings.patch_embeddings,
# )
# model.image_tokenizer.model.encoder = VitModelEncoderWrapper(compiled_vit_model_encoder)
# model.image_tokenizer.model.pooler = VitModelPoolerWrapper(compiled_vit_model_pooler)

# model.tokenizer = TokenizerWrapper(compiled_tokenizer, model.tokenizer)
# model.backbone = BackboneWrapper(compiled_backbone)
# model.post_processor = PostProcessorWrapper(compiled_post_processor)

rembg_session = rembg.new_session()

# 입력 이미지 체크
def check_input_image(input_image):
    if input_image is None:
        raise gr.Error("No image uploaded!")


# 입력 이미지 전처리
def preprocess(input_image, do_remove_background, foreground_ratio):
    def fill_background(image):
        image = np.array(image).astype(np.float32) / 255.0
        image = image[:, :, :3] * image[:, :, 3:4] + (1 - image[:, :, 3:4]) * 0.5
        image = Image.fromarray((image * 255.0).astype(np.uint8))
        return image

    if do_remove_background:
        image = input_image.convert("RGB")
        image = remove_background(image, rembg_session)
        image = resize_foreground(image, foreground_ratio)
        image = fill_background(image)
    else:
        image = input_image
        if image.mode == "RGBA":
            image = fill_background(image)
    return image

# 3D 모델 생성 함수 
def generate(image):
    scene_codes = model(image, device = "cpu")  # the device is provided for the image processor
    mesh = model.extract_mesh(scene_codes)[0]
    mesh = to_gradio_3d_orientation(mesh)
    #mesh_path = tempfile.NamedTemporaryFile(suffix=".obj", delete=False)
    mesh_path = "output/image_to_3d.obj"
    # mesh.export(mesh_path.name)
    mesh.export(mesh_path)
    print("export complete")
    return mesh_path

def image_to_3D(image_path):
    # OpenVINO의 코어를 가져옴
    core = ov.Core()
    device = "CPU"

    # 모델 컴파일 
    compiled_vit_patch_embeddings = core.compile_model(VIT_PATCH_EMBEDDINGS_OV_PATH, device)
    compiled_vit_model_encoder = core.compile_model(VIT_ENCODER_OV_PATH, device)
    compiled_vit_model_pooler = core.compile_model(VIT_POOLER_OV_PATH, device)

    compiled_tokenizer = core.compile_model(TOKENIZER_OV_PATH, device)
    compiled_backbone = core.compile_model(BACKBONE_OV_PATH, device)
    compiled_post_processor = core.compile_model(POST_PROCESSOR_OV_PATH, device)

    model.image_tokenizer.model.embeddings.patch_embeddings = VitPatchEmdeddingsWrapper(
        compiled_vit_patch_embeddings,
        model.image_tokenizer.model.embeddings.patch_embeddings,
    )
    model.image_tokenizer.model.encoder = VitModelEncoderWrapper(compiled_vit_model_encoder)
    model.image_tokenizer.model.pooler = VitModelPoolerWrapper(compiled_vit_model_pooler)

    model.tokenizer = TokenizerWrapper(compiled_tokenizer, model.tokenizer)
    model.backbone = BackboneWrapper(compiled_backbone)
    model.post_processor = PostProcessorWrapper(compiled_post_processor)

    # 이미지 불러오기 
    input_image = load_image(image_path)
    # 이미지 전처리
    processed_image = preprocess(input_image, True, 0.85)
    # 3D 모델 생성 
    result = generate(processed_image)

    return result

# image_to_3D("output/sketch_to_image.jpg")
