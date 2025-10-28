from .mixins import CompiledLanguageExecutorMixin
from ..interface import CodeExecutor


class KotlinCodeExecutor(CompiledLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-kotlin-sqlite:1.9.0'
    language = 'kotlin'
    version = '1.9.0'
    display_name = 'Kotlin 1.9.0'

    id = CodeExecutor.create_id('kotlin', '1.9.0')

    SOURCE_FILE_NAME_TEMPLATE = 'Main.kt'
    EXECUTABLE_FILE_NAME_TEMPLATE = 'MainKt'

    # Compile to jar
    COMPILE_COMMAND_TEMPLATE = (
        'kotlinc -J-Xmx1024m -J-Xms256m \
            -J-Dorg.sqlite.tmpdir=/sandbox/tmp \
                  -cp "/app/lib/*" {source_file} \
                    -include-runtime -d /sandbox/app.jar'
    )

    # Run with stdin
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = (
        'java -Xms256m -Xmx1024m \
            -Dorg.sqlite.tmpdir=/sandbox/tmp \
            -Dorg.sqlite.lib.path=/sandbox/sqlite-lib \
                -Dsqlite.purejava=true \
                  -Djava.io.tmpdir=/sandbox/tmp \
                    -cp "/app/lib/*:/sandbox/app.jar" \
                      {executable_file}'
    )

    # Run with file input
    RUN_COMMAND_FILE_INPUT_TEMPLATE = (
        'java -Xms256m -Xmx1024m \
            -Dorg.sqlite.tmpdir=/sandbox/tmp \
            -Dorg.sqlite.lib.path=/sandbox/sqlite-lib \
                -Dsqlite.purejava=true \
                  -Djava.io.tmpdir=/sandbox/tmp \
                    -cp "/app/lib/*:/sandbox/app.jar" \
                      {executable_file} {input_file}'
    )
