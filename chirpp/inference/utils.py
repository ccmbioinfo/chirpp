import gc

import torch


def cleanup_cuda():
    """Fully clears GPU memory."""
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
    torch.cuda.synchronize()
    gc.collect()


def cleanup_model(model):
    """Moves model to CPU, deletes it, and clears CUDA."""
    if model is not None:
        try:
            model.to("cpu")
        except Exception:
            pass
        del model
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
    torch.cuda.synchronize()
