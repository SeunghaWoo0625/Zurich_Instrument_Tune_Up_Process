from laboneq import workflow
from laboneq.workflow.logbook import FolderStore

@workflow.workflow_options
class TuneUpProcessOptions:
    id:str = "default" # 실험의 id
    author:str = "student" # 실험 수행자

    do_analysis : bool = True

    show_figure:bool = False # plt.show() 실행할지
    update_parameters:bool = True # 실험이 수행되면서 자동으로 fitting 되는 값들로 qubit parameter들 변경
    save_pulse_sheet:bool = True # compile이 끝나고 pulse sheet 저장할지
    save_figure:bool = True # 각 실험마다 최종 figure 저장할지
    save_results:bool = True # 각 실험마다 최종 result 저장할지
    save_simulation:bool = False # complie하고 시물레이션 저장할지

@workflow.task_options
class TimeOfFlightExperimentOptions:
    count: int = 10             
    Delay_time_begin:float = 0e-9
    Delay_time_end:float = 100e-9
    Delay_time_points:int = 11
    Measure_length:float = 100e-9
    passive_reset_delay = 70e9
