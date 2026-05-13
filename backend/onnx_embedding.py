"""
Lightweight ONNX-based embedding model.
Replaces sentence-transformers + PyTorch (~3-4GB) with onnxruntime + tokenizers (~200MB).
Produces identical embeddings using the same all-MiniLM-L6-v2 model.
"""

import os
import logging
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

# Default model configuration
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MAX_LENGTH = 256


class OnnxEmbeddingModel:
    """Drop-in replacement for SentenceTransformer using ONNX Runtime.
    
    Usage:
        model = OnnxEmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        embedding = model.encode("Hello world")  # numpy array (384,)
    """

    def __init__(self, model_name: str = None):
        """Initialize ONNX embedding model.
        
        Args:
            model_name: HuggingFace model name (e.g. "all-MiniLM-L6-v2" or 
                        "sentence-transformers/all-MiniLM-L6-v2").
                        Short names are auto-prefixed with "sentence-transformers/".
        """
        # Normalize model name
        if model_name and "/" not in model_name:
            model_name = f"sentence-transformers/{model_name}"
        self.model_name = model_name or DEFAULT_MODEL_NAME
        self.max_length = DEFAULT_MAX_LENGTH

        # Download and load model files
        logger.info(f"Loading ONNX embedding model: {self.model_name}")
        self._load_model()
        logger.info(f"ONNX embedding model ready: {self.model_name}")

    def _load_model(self):
        """Download model files from HuggingFace and initialize ONNX session."""
        # Download ONNX model file
        onnx_path = hf_hub_download(
            repo_id=self.model_name,
            filename="onnx/model.onnx",
        )

        # Download tokenizer file
        tokenizer_path = hf_hub_download(
            repo_id=self.model_name,
            filename="tokenizer.json",
        )

        # Initialize ONNX Runtime session (CPU only)
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = os.cpu_count() or 4
        self.session = ort.InferenceSession(
            onnx_path,
            sess_options,
            providers=["CPUExecutionProvider"],
        )

        # Initialize tokenizer
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_truncation(max_length=self.max_length)
        self.tokenizer.enable_padding(length=self.max_length)

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text string into an embedding vector.
        
        Args:
            text: Input text to encode.
            
        Returns:
            numpy array of shape (embedding_dim,) — e.g. (384,) for MiniLM.
        """
        # Tokenize
        encoded = self.tokenizer.encode(text)
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        token_type_ids = np.array([encoded.type_ids], dtype=np.int64)

        # Run ONNX inference
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        }
        outputs = self.session.run(None, inputs)

        # outputs[0] shape: (1, seq_len, hidden_dim)
        token_embeddings = outputs[0]

        # Mean pooling: average token embeddings, weighted by attention mask
        mask_expanded = attention_mask[:, :, np.newaxis].astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.sum(mask_expanded, axis=1)
        sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)
        mean_pooled = sum_embeddings / sum_mask

        # L2 normalize
        norm = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
        norm = np.clip(norm, a_min=1e-9, a_max=None)
        normalized = mean_pooled / norm

        return normalized[0]  # Return 1D array (embedding_dim,)
