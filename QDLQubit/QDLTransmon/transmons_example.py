#%%
from laboneq_applications.qpu_types.tunable_transmon import TunableTransmonOperations, TunableTransmonQubit, TunableTransmonQubitParameters

Transmon = TunableTransmonQubit(
    uid = "test",
    signals = {
        "drive": "drive",
        "drive_ef": "drive_ef"
        "measure" : "measure", 
        "acquire" : "acquire",
    }
)
#%%