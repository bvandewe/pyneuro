# Desktop Controller

REST API to remotely control a Desktop (i.e. the Docker Host running the controller) over HTTP.

The Controller must:

1. Register itself periodically (via CloudEvent) to the Desktops Registry (providing its IP address as the identifier to the Registry)
2. Securely expose a set of `Commands` and `Queries` via a REST API (with OpenAPI 3.x specs) that enable remote control for the Desktop's `HostInfo` and `UserInfo` (wrapping Linux Shell commands as HTTP Requests)
3. Maintain various local files (e.g. `/data/hostinfo.json`, `/data/userinfo.json`) that other apps (on the Desktop VM) may rely upon (Screen Logger).
4. Trigger remote execution of custom Shell scripts to be run on the Desktop VM (not the controller's container!)

[[_TOC_]]

## Overview

### Controller's Interactions

![Desktop Controller Interactions](img/DesktopController_Interactions.png)

### Controller's Context

![Desktop Controller](img/DesktopController.png)

## Design

![Design](img/design.png)
  
## Development

### Setup

```sh

# 0. Prerequisites:
#    Have Python 3.12 installed
# 
#    - Create/Activate a local python environment (e.g. with pyenv)
#      pyenv virtualenv 3.12.2 desktop-controller
#      pyenv activate desktop-controller
# 
#    - Start Docker Desktop locally
#
# 1. Clone the repository
cd ~/

git clone git@....

cd desktop-controller

# pip install pre-commit
pre-commit install

# pip install poetry
poetry lock && poetry install 

# 2. Start the docker-compose stack
# sudo apt-get install make
make up

# 3. Connect the vscode debugger to the running container
# From vscode: hit F5 (ensure that the "Run and Debug" launcher is set to "Python: Remote Attach")

# 4. Open the SwaggerUI at http://localhost:9781/api/docs

# 5. Add a Breakpoint, e.g. in api.controllers.userinfo_controller.py:29...

# 6. Send a test request :)

# 7. Enjoy live debugging on your local development
```

### Code Contribution

1. Clone `main` branch
2. Create new branch, e.g. `feat-cmd-userinfo` or `fix-linux-cmd`
3. Push the new branch to Gitlab and create a Merge Request into `main`
4. Document the review
5. Approve and merge (may discard the branch if needed)

### Release Process

1. Refer to [Semantic Versioning](https://semver.org/)
2. Create new Tag in Gitlab > Repository > Tags > [New Tag]()
3. This will trigger Gitlab CI to publish a new container image based on the latest commit in the `main` branch and will be named as per the new Tag.
4. Test the image locally: `docker run -p 8080:80 desktop-controller:latest` then browse to http://localhost:8080/api/docs

### Settings

Required configuration:

- create new SSH key pair
- install the private key into the container and the public key into the DockerHost/SSH server
  - mount the SSH private key to `:/app/id_rsa` when starting the container
  - add the pub key to the DockerHost's `~/.ssh/authorized_keys`
- add env var `DOCKER_HOST_USER_NAME` with the sys-admin' username on the DockerHost!

See [App Settings](#app-settings).

## Testing

The API has a sample `Command` that ultimately resolves to remotely run `~/test_shell_script_on_host.sh -i {user_input}` on the DockerHost. 

See [sample_bin/test_shell_script_on_host.sh](sample_bin/test_shell_script_on_host.sh).

E.g.: Install with

```sh
# copy the sample shell script on the Docker Host' user' home folder
cp sample_bin/test_shell_script_on_host.sh ~/test_shell_script_on_host.sh

# set permissions to execute
chmod a+x ~/test_shell_script_on_host.sh

# set ownership
chown $USERNAME:staff ~/test_shell_script_on_host.sh

# test run as user:
~/test_shell_script_on_host.sh -i "my input value"

Adding a new line my input value to /tmp/test.txt...

# verify local file on Docker Host: 
cat /tmp/test.txt

UserInput: my input value

```

### test_shell_script_on_host.sh

See [sample_bin/test_shell_script_on_host.sh](sample_bin/test_shell_script_on_host.sh).

This test script just adds a line to a file `/tmp/test.txt`.

```sh
#!/bin/bash

# test_shell_script_on_host.sh

if [ $# -lt 2 ]; then
  echo "Error: Please provide an argument after the -i flag."
  exit 1
fi

if [ "$1" != "-i" ]; then
  echo "Error: Please use the -i flag followed by your argument."
  exit 1
fi

argument="$2"

echo "Adding a new line $argument to /tmp/test.txt..."

echo "UserInput: $argument" >> /tmp/test.txt

```

### Call Test Endpoint

The HTTP `Command` runs a SSH client that simply connects to the DockerHost at `host.docker.internal` (with preconfigured username and SSH keys) and runs a custom command_line.

From [SwaggerUI](http://localhost:9781/api/docs#/Custom/run_test_write_file_on_host_api_v1_custom_test_shell_script_on_host_sh_post)

`http://localhost:9781/api/docs#/Custom/run_test_write_file_on_host_api_v1_custom_test_shell_script_on_host_sh_post`

From Curl: (will need `Authorization` header with JWT, see [API Auth](#api-authentication))

```curl
curl -X 'POST' \
  'http://localhost:9781/api/v1/custom/test/shell_script_on_host.sh' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user_input": "my input value"
}'
```

```json
# 201	Response body
{
  "command_line": "~/test_shell_script_on_host.sh -i my_input_value",
  "stdout": [
    "Adding a new line my_input_value to /tmp/test.txt..."
  ],
  "stderr": [],
  "aggregate_id": "4c660c0572d8449598ee5fde58e04423",
  "success": true
}
```

### API Authentication

We're using Keycloak as the IDP. See `deployment/keycloak/realm-config.json` for sample keycloak config.

The intent is that "whoever" wants to remotely control a desktop first needs to get a valid token from the common Keycloak instance (which is the one that the VDI/BYOD Desktops - ie. DockerHosts have access to!).

Local testings can be done with a local/dev Keycloak instance. Just include it in `docker-compose.yml`!


```yml
version: "3.4"

name: mozart-dev
services:
  # http://localhost:9780
  keycloak97:
    image: jboss/keycloak
    environment:
      - KEYCLOAK_USER=admin
      - KEYCLOAK_PASSWORD=admin
      - KEYCLOAK_IMPORT=/tmp/realm-export.json
    volumes:
      - ./deployment/keycloak/realm-config.json:/tmp/realm-export.json
    ports:
      - 9780:8080
    networks:
      - desktopcontrollernet
```

Login at http://localhost:9780 using `admin`:`admin`

## Source Code

![Structure](img/src-Code_Structure.png)

### Context

![Context](img/src-Context.png)

### Containers

![Container](img/src-Container.png)

### Components

![Components](img/src-Components.png)

### Code

![Code](img/src-Code.png)

#### App Settings

```yml
    environment:
      APP_TITLE: Remote Desktop Controller
      LOCAL_DEV: true
      LOG_LEVEL: DEBUG
      
      CLOUD_EVENT_SINK: http://event-player97/events/pub
      CLOUD_EVENT_SOURCE: https://desktop-controller.domain.com
      CLOUD_EVENT_TYPE_PREFIX: com.domain.desktop-controller
      
      OAUTH2_SCHEME: client_credentials  # authorization_code or client_credentials
      JWT_AUTHORITY: http://keycloak97/auth/realms/mozart
      JWT_SIGNING_KEY: MIIBIj...copy_from_keycloak...elJ3dvQIDAQAB
      JWT_AUDIENCE: desktops
      REQUIRED_SCOPE: api
      
      SWAGGER_UI_JWT_AUTHORITY: http://localhost:9780/auth/realms/mozart
      SWAGGER_UI_CLIENT_ID: desktop-controller
      SWAGGER_UI_CLIENT_SECRET: 6Wbr0V1TtgEUPUCRSqHh1T0vYuVyG0aa
      
      USER_INFO_FILE_NAME: '/tmp/userinfo.json'
      HOST_INFO_FILE_NAME: '/tmp/hostinfo.json'
      DOCKER_HOST_USER_NAME: bvandewe  # UPDATE TO YOUR LOCAL USERNAME!
      DOCKER_HOST_HOST_NAME: host.docker.internal

```

Set corresponding `ENV VARS` in `docker-compose.yml`.

[Pydantic settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) automatically parses environment variables, see [./src/api/settings.py](./src/api/settings.py).

```python
# ./src/api/settings.py

from neuroglia.hosting.abstractions import ApplicationSettings
from pydantic import ConfigDict


class DesktopControllerSettings(ApplicationSettings):
    model_config = ConfigDict(extra="allow")

    required_scopes: str
    jwt_authority: str
    jwt_signing_key: str
    jwt_audience: str = "desktops"
    docker_host_user_name: str = "sys-admin"
    userinfo_filename: str = "/app/data/userinfo.json"
    ...

app_settings = DesktopControllerSettings(_env_file=".env")

```

#### App Bootup

The `main.py` file pre-loads all required services using the Dependency Injection mechanism from the neuroglia framework.

API Controllers and Application Handlers may then declare any dependencies in their constructor (`def __init__(self, my_dependency: RegisteredDependency)`) and the framework will provide the instance!

See [Dependency Injection](#dependency-injection).

```python
# ./src/main.py
...
builder = WebApplicationBuilder()

# required shared resources
Mapper.configure(builder, application_modules)
Mediator.configure(builder, application_modules)
JsonSerializer.configure(builder)
CloudEventIngestor.configure(builder, application_modules)
CloudEventPublisher.configure(builder)

# custom shared resources
# 
# ADD ANY REQUIRED RESOURCE
builder.services.add_scoped(paramiko.SSHClient, paramiko.SSHClient)
builder.services.add_scoped(SecuredDockerHost, SecuredDockerHost)
builder.services.add_singleton(DockerHostSshClientSettings, singleton=DockerHostSshClientSettings(username=builder.settings.docker_host_user_name))
builder.services.add_scoped(DockerHostCommandRunner, DockerHostCommandRunner)

# app
app = builder.build()
...
app.run()
```

#### Dependency Injection

1. Add a Custom Service source code file (likely in any of the `application_modules` folder in `./src/api/controllers` or `./src/application/commands` or `./src/application/queries` or `./src/application/events`) that requires a `Dependency`:

  ```python
  # ./src/application/services/docker_host_command_runner.py
  ...
  class DockerHostCommandRunner:
      def __init__(self, secured_docker_host: SecuredDockerHost):  # Declare Dependencies!
          self.secured_docker_host = secured_docker_host
 
      secured_docker_host: SecuredDockerHost  # Injected when handling a Command!

      async def run(self, command: HostCommand) -> dict[str, Any]:
          data = {}
          await self.secured_docker_host.connect()
          stdout, stderr = await self.secured_docker_host.execute_command(command)
          await self.secured_docker_host.close()
          stdout_lines = [line.strip() for line in stdout.splitlines() if line.strip()]
          data = {"command_line": command.line, "stdout": stdout_lines, "stderr": stderr.splitlines() if stderr else []}
          return data
  ...
  ```

2. Add the source code for the dependency itself (likely in `./src/integration/services`!). It may also include other dependencies! (e.g. `DockerHostSshClientSettings`!!)
  
  ```python
  # ./src/integration/services/secured_docker_host.py
  ...

  class DockerHostSshClientSettings(BaseModel):
      username: str
      hostname: str = "host.docker.internal"
      port: int = 22
      private_key_filename: str = "/app/id_rsa"
  ...
  class SecuredDockerHost:
      """Service that Securely provides access to the Docker Host's Shell via SSH."""

      def __init__(self, ssh_client: paramiko.SSHClient, ssh_client_settings: DockerHostSshClientSettings):
          self.hostname: str = ssh_client_settings.hostname
          self.port: int = ssh_client_settings.port
          self.username: str = ssh_client_settings.username
          self.private_key_filename: str = ssh_client_settings.private_key_filename
          self.ssh_client: paramiko.SSHClient = ssh_client
          self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

      async def connect(self):
          ...

      async def execute_command(self, command: HostCommand):
          async def run_command(command_line: str):
              ...

          stdout, stderr = await run_command(command.line)
          return stdout.decode(), stderr.decode()

      async def close(self):
          ...
  ```

3. Register its service_type (`singleton`, `scoped`, `transient`) in the `main.py` bootup script

  ```python
  # ./src/main.py
  ...
  builder.services.add_scoped(paramiko.SSHClient, paramiko.SSHClient)
  builder.services.add_scoped(SecuredDockerHost, SecuredDockerHost)
  builder.services.add_singleton(DockerHostSshClientSettings, singleton=DockerHostSshClientSettings(username=builder.settings.docker_host_user_name))
  builder.services.add_scoped(DockerHostCommandRunner, DockerHostCommandRunner)
  ...
  ```

4. Declare it as a dependency in a consumer Service, e.g. Application's `CommandHandler`: 

  > Note how the `DockerHostCommandRunner` is just declared as a dependency in the constructor function `__init__`!
  > This is the same for the other dependencies (`CloudEventBus`, `CloudEventPublishingOptions`)

  ```python

  @map_from(TestHostScriptCommandDto)
  @map_to(TestHostScriptCommandDto)
  @dataclass
  class TestHostScriptCommand(Command):
      user_input: str


  class TestHostScriptCommandsHandler(CommandHandler[TestHostScriptCommand, OperationResult[Any]]):
      """Represents the service used to handle UserInfo-related Commands"""

      cloud_event_bus: CloudEventBus
      """ Gets the service used to observe the cloud events consumed and produced by the application """

      cloud_event_publishing_options: CloudEventPublishingOptions
      """ Gets the options used to configure how the application should publish cloud events """

      docker_host_command_runner: DockerHostCommandRunner

      def __init__(self, cloud_event_bus: CloudEventBus, cloud_event_publishing_options: CloudEventPublishingOptions, docker_host_command_runner: DockerHostCommandRunner):
          self.cloud_event_bus = cloud_event_bus
          self.cloud_event_publishing_options = cloud_event_publishing_options
          self.docker_host_command_runner = docker_host_command_runner

      async def handle_async(self, command: TestHostScriptCommand) -> OperationResult[Any]:
          command_id = str(uuid.uuid4()).replace("-", "")
          command_line = HostCommand()
          data = {}
          try:
              line = f"~/test_shell_script_on_host.sh -i {command.user_input.replace(' ', '_')}"
              log.debug(f"TestHostScriptCommand Line: {line}")
              await self.publish_cloud_event_async(DesktopHostCommandReceivedIntegrationEventV1(aggregate_id=command_id, command_line=line))

              command_line.line = line
              data = await self.docker_host_command_runner.run(command_line)
              data.update({"aggregate_id": command_id})
              log.debug(f"TestHostScriptCommand: {data}")

              await self.publish_cloud_event_async(DesktopHostCommandExecutedIntegrationEventV1(**data))
              data.update({"success": True}) if len(data["stderr"]) == 0 else data.update({"success": False})
              return self.created(data)

          except Exception as ex:
              return self.bad_request(f"Exception when trying to run a shell script on the host: {command_line.line}: {data}: {ex}")
  ```

#### API Controllers

- inherits ControllerBase

```python
# ./src/api/controllers/host_controller.py

class HostController(ControllerBase):
    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        ControllerBase.__init__(self, service_provider, mapper, mediator)

    @post("/info", response_model=Any, status_code=201, responses=ControllerBase.error_responses)
    async def set_host_info(self, command_dto: SetHostInfoCommandDto, token: str = Depends(validate_token)) -> Any:
        """Sets data of the hostinfo.json file."""
        log.debug(f"set_host_info: command_dto:{command_dto}, token={token}")
        return self.process(await self.mediator.execute_async(self.mapper.map(command_dto, SetHostInfoCommand)))

    @get("/info", response_model=Any, status_code=201, responses=ControllerBase.error_responses)
    async def get_host_info(self):
        query = ReadHostInfoQuery()
        log.debug(f"get_host_info: query:{query}")
        return self.process(await self.mediator.execute_async(query))

```