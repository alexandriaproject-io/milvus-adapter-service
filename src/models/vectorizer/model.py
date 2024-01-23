from src.logger import log
from sentence_transformers import SentenceTransformer


class SentenceModel:
    def __init__(self, model_path, device=None, auth_token=None, cache_folder=None):
        self.isReady = False
        self.tokenizer = None
        self.model = None
        self.model_path = model_path
        self.cache_folder = cache_folder
        self.device = device
        self.auth_token = auth_token

    def load_model(self):
        log.info(f"Loading model: {self.model_path}")
        self.model = SentenceTransformer(
            model_name_or_path=self.model_path,
            cache_folder=self.cache_folder,
            use_auth_token=self.auth_token,
            device=self.device,
        )
        self.embed_text("Warmup run")  # makes sure the model is loaded and capable of running

    def embed_text(self, text=None, texts_list=None):
        if text:
            return self.model.encode([text], convert_to_tensor=True)[0]
        elif texts_list:
            return self.model.encode(texts_list, convert_to_tensor=True)
