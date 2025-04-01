import logging
from dataclasses import dataclass
from typing import Any

from neuroglia.core import OperationResult
from neuroglia.mediation import Command, CommandHandler
from neuroglia.serialization.json import JsonSerializer

from application.services import DockerHostCommandRunner
from integration.services import HostCommand

log = logging.getLogger(__name__)


@dataclass
class SetHostLockCommand(Command):
    script_name: str = "/usr/local/bin/lock.sh"


class HostLockCommandsHandler(CommandHandler[SetHostLockCommand, OperationResult[Any]]):
    """Represents the service used to handle HostLock-related Commands"""

    def __init__(self, docker_host_command_runner: DockerHostCommandRunner, json_serializer: JsonSerializer):
        self.docker_host_command_runner = docker_host_command_runner
        self.json_serializer = json_serializer

    docker_host_command_runner: DockerHostCommandRunner

    json_serializer: JsonSerializer

    async def handle_async(self, script: SetHostLockCommand) -> OperationResult[Any]:
        command_line = HostCommand()
        data = {}
        try:
            log.debug(f"Running the HostLock script.")
            command_line.line = script.script_name
            data = await self.docker_host_command_runner.run(command_line)
            data.update({"success": True}) if len(data["stderr"]) == 0 else data.update({"success": False})
            return self.created(data)

        except Exception as ex:
            return self.bad_request(f"Exception when running the HostLock script: command_line={command_line} Exception={ex}")
