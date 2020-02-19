from enum import Enum
import typing as ty
from uuid import uuid1

import reapy as rpr
from reapy import reascript_api as RPR

from config import EXT_SECTION


class ProjectType(Enum):
    value: str

    normal: str = 'normal'
    master: str = 'master'
    slave: str = 'slave'


class TrackedTrack(rpr.Track):
    pass


class Project(rpr.Project):
    def __init__(self, id_: ty.Optional[int] = None, index: int = -1) -> None:
        super().__init__(id_, index)
        self._info = ProjectInfo()
        self.type_: ProjectType = self._info._get_type(self)
        self._tracked_tracks: ty.List[TrackedTrack] = []


class ProjectInfoMeta(type):
    _instance: ty.Optional['ProjectInfo'] = None

    def __call__(cls) -> 'ProjectInfo':  # type:ignore
        if not cls._instance:
            cls._instance = super().__call__()
        return ty.cast(ProjectInfo, cls._instance)


class ProjectInfo(metaclass=ProjectInfoMeta):
    _master_project: ty.Optional[rpr.Project]
    _connected_fx_name: str = 'ReaStream'

    class no_ext_state(Exception):
        def __init__(self, key: str) -> None:
            super().__init__(f'there is no "{key}" ext state')

    def __init__(self) -> None:
        self._active_project = rpr.Project(id=-1)
        self._projects = rpr.get_projects()
        self._master_project = None

    @rpr.inside_reaper()
    def get_ext_state(
        self, project: rpr.Project, key: str, section: str = EXT_SECTION
    ) -> str:
        size_str: str
        (_, _, _, _, size_str, _) = RPR.GetProjExtState(  # type:ignore
            project.id, section, key+'_size', 'valOutNeedBig', 1001
        )
        if not size_str:
            raise self.no_ext_state(f'{section}:{key}')
        size = int(size_str)
        (_, _, _, _, result, _) = RPR.GetProjExtState(  # type:ignore
            project.id, section, key, 'valOutNeedBig', size+1
        )
        return ty.cast(str, result)

    @rpr.inside_reaper()
    def set_ext_state(
        self,
        project: rpr.Project,
        key: str,
        value: str,
        section: str = EXT_SECTION
    ) -> int:
        size: int = len(value)
        RPR.SetProjExtState(  # type:ignore
                project.id,  # noob formatting comment
                section,
                key,
                value
            )
        size_str: str = str(str(size).encode().zfill(1000), 'utf-8')
        RPR.SetProjExtState(  # type:ignore
                project.id,  # noob formatting comment
                section,
                key+'_size',
                size_str
            )
        return size

    def run(self) -> None:
        ...

    def _get_type(self, project: rpr.Project) -> 'ProjectType':
        try:
            type_str = self.get_ext_state(project, 'project_type')
        except self.no_ext_state:
            return ProjectType.normal
        return ProjectType(type_str)

    def _set_type(self, project: rpr.Project, pr_type: 'ProjectType') -> None:
        self.set_ext_state(project, 'project_type', pr_type.value)

    def _set_id(self, project: rpr.Project) -> str:
        id_ = uuid1().hex
        self.set_ext_state(project, 'id', id_)
        return id_

    def _get_id(self, project: rpr.Project) -> str:
        id_ = self.get_ext_state(project, 'id')
        if not id_:
            raise RuntimeError(
                'this is normal project, this should not be happend'
            )
        return id_

    @rpr.inside_reaper()
    def get_info(self, project: rpr.Project) -> ty.Dict[str, object]:
        result: ty.Dict[str, object] = {
            'name': project.name,
            'type': self._get_type(project).value,
            'id': self._get_id(project)
        }
        return result
