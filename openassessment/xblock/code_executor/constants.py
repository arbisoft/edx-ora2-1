DEFAULT_LIMITS = {
    # CPU time in seconds, None for unlimited
    'cputime': 30,
    # Real time in seconds, None for unlimited
    'realtime': 35,
    # Memory in megabytes, None for unlimited
    'memory': 512,
    # limit the max processes the sandbox can have
    # -1 or None for unlimited(default)
    'processes': -1,
}

# Language-specific limits mapped by executor ID
LIMITS = {
    # Python executors - faster execution, lower memory
    'python:3.12': {
        'cputime': 20,
        'realtime': 25,
        'memory': 256,
        'processes': -1,
    },
    'python-ml:3.12': {
        'cputime': 60,
        'realtime': 65,
        'memory': 1024,  # ML libraries need more memory
        'processes': -1,
    },

    # Compiled languages - need compilation time + execution
    'cpp:g++-9.3': {
        'cputime': 30,
        'realtime': 35,
        'memory': 512,
        'processes': -1,
    },
    'java:openjdk-19': {
        'cputime': 35,
        'realtime': 40,
        'memory': 768,  # JVM needs more memory
        'processes': -1,
    },
    'kotlin:1.9.0': {
        'cputime': 40,
        'realtime': 45,
        'memory': 1024,  # Kotlin compilation is memory-intensive
        'processes': -1,
    },
    'dotnet:8.0': {
        'cputime': 35,
        'realtime': 40,
        'memory': 768,
        'processes': -1,
    },
    'swift:6.0.3-amazonlinux2': {
        'cputime': 35,
        'realtime': 40,
        'memory': 768,
        'processes': -1,
    },

    # Scripted languages
    'javascript:nodejs-sqlite-18.14.1': {
        'cputime': 20,
        'realtime': 25,
        'memory': 384,
        'processes': -1,
    },
    'php:8.3.3': {
        'cputime': 20,
        'realtime': 25,
        'memory': 256,
        'processes': -1,
    },
}
