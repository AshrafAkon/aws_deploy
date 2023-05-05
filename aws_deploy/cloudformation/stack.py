from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union

STACK_FAILED_STATUS_LIST = [
    'CREATE_FAILED',
    'ROLLBACK_COMPLETE',
    'DELETE_FAILED',
    'UPDATE_FAILED',
    'UPDATE_ROLLBACK_FAILED',
    'ROLLBACK_FAILED'
    # 'UPDATE_ROLLBACK_COMPLETE'
]


@dataclass
class OutputData:
    OutputKey: str
    OutputValue: str
    Description: str
    ExportName: Optional[str]


@dataclass
class CloudformationStack:
    StackId: str
    StackName: str
    Description: str
    Parameters: List[Dict[str, Optional[Union[str, bool]]]]
    CreationTime: datetime
    RollbackConfiguration: Dict[str, Union[List[Dict[str, str]], int]]
    StackStatus: str
    DisableRollback: bool
    NotificationARNs: List[str]
    Capabilities: List[str]
    Outputs: Optional[List[OutputData]]
    Tags: List[Dict[str, str]]
    EnableTerminationProtection: bool
    DriftInformation: Dict[str, Union[str, datetime]]

    ChangeSetId: Optional[str] = None
    DeletionTime: Optional[datetime] = None
    LastUpdatedTime: Optional[datetime] = None
    StackStatusReason: Optional[str] = None
    TimeoutInMinutes: Optional[int] = None
    RoleARN: Optional[str] = None
    ParentId: Optional[str] = None
    RootId: Optional[str] = None

    def failed(self):
        return self.StackStatus in STACK_FAILED_STATUS_LIST

    def updating(self):
        return self.StackStatus == 'UPDATE_IN_PROGRESS'

    @classmethod
    def from_dict(cls, val):
        if val.get('Outputs'):
            val['Outputs'] = [OutputData(**x) for x in val['Outputs']]
        return cls(**val)


# @dataclass
# class CloudformationStack:
#     stack_info: Optional[StackInfo]

#     def __init__(self, template: CloudformationTemplate) -> None:

#         self.template: CloudformationTemplate = template

#     # def get_full_name(self, short_name: str, t_type: str):
#     #     try:
#     #         if t_type == 'core':
#     #             return config.core_templates_map[short_name]
#     #         # elif t_type == 'backup':
#     #         #     return config.backup_templates_map[short_name]
#     #         else:
#     #             return config.service_templates_map[short_name]
#     #     except KeyError:
#     #         raise TemplateNotFoundException(
#               'Template shortname not found.')
