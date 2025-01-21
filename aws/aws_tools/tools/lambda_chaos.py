from kubiya_sdk.tools import Arg
from .base import AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry
import json
import random
import time
import threading
import queue
import sys

class MemoryLeakSimulator:
    def __init__(self):
        self.data = []
        
    def leak_memory(self):
        while True:
            # Create large objects that won't be garbage collected
            self.data.extend([object() for _ in range(100000)])
            time.sleep(0.1)

class ConcurrencyExhauster:
    def __init__(self, limit=100):
        self.concurrent_executions = 0
        self.limit = limit
        self.lock = threading.Lock()
        self.error_queue = queue.Queue()
        
    def execute(self):
        with self.lock:
            if self.concurrent_executions >= self.limit:
                raise RuntimeError("Lambda concurrency limit exceeded")
            self.concurrent_executions += 1
        
        try:
            # Simulate various Lambda execution failures
            if random.random() < 0.8:
                error_types = [
                    ("Timeout", "Function execution timed out after 15 minutes"),
                    ("Memory", "Memory limit exceeded: 3008 MB"),
                    ("Throttle", "Lambda function throttled due to account concurrency limit"),
                    ("Permission", "Lambda execution role has insufficient permissions"),
                    ("Network", "ENI attachment failed in Lambda VPC configuration"),
                    ("Runtime", "Runtime.ImportModuleError: Unable to import module 'handler'"),
                    ("Initialization", "Lambda initialization failed: unable to load function code"),
                    ("Configuration", "Environment variables exceed size limit"),
                    ("SDK", "AWS SDK encountered too many requests"),
                    ("Cold Start", "Container initialization timed out")
                ]
                error_type, message = random.choice(error_types)
                self.error_queue.put({
                    "errorType": error_type,
                    "errorMessage": message,
                    "stackTrace": self.generate_stack_trace()
                })
                raise Exception(f"Lambda Error: {error_type} - {message}")
        finally:
            with self.lock:
                self.concurrent_executions -= 1
                
    @staticmethod
    def generate_stack_trace():
        frames = [
            "at Runtime.handler (/var/task/index.js:1:1)",
            "at Runtime.handleOnce (/var/runtime/Runtime.js:66:25)",
            "at process._tickCallback (internal/process/next_tick.js:68:7)",
            "at Function.Module.runMain (internal/modules/cjs/loader.js:745:11)",
            "at startup (internal/bootstrap/node.js:283:19)",
            at Object.<anonymous> (/var/task/node_modules/aws-sdk/lib/request.js:31:12)"
        ]
        return random.sample(frames, random.randint(2, len(frames)))

# Start memory leak in background
memory_leaker = MemoryLeakSimulator()
threading.Thread(target=memory_leaker.leak_memory, daemon=True).start()

# Create concurrency exhaustion simulator
concurrency = ConcurrencyExhauster(limit=5)

lambda_chaos_tool = AWSSdkTool(
    name="lambda_chaos_tool",
    description="Creates chaos in serverless functions and Lambda executions",
    content="""
import boto3
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def generate_event_payload():
    # Generate problematic event payloads
    payload_types = [
        lambda: {"data": "x" * (6 * 1024 * 1024)},  # Oversized payload
        lambda: {"nested": {"a": {"b": {"c": {"d": {"e": "deep nesting"}}}}}} * 100,
        lambda: {"malformed": float('inf')},  # Non-serializable JSON
        lambda: {"timeout": time.sleep(900)},  # Function timeout
        lambda: {"recursive": {"self": None}},  # Circular reference
    ]
    return random.choice(payload_types)()

def simulate_lambda_chaos(function_name):
    lambda_client = boto3.client('lambda')
    
    def invoke_function():
        try:
            # Try to invoke Lambda with problematic payload
            payload = generate_event_payload()
            
            # Simulate concurrent executions
            concurrency.execute()
            
            # Create malformed request
            response = lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(payload),
                InvocationType=random.choice(['Event', 'RequestResponse']),
                LogType='None' if random.random() < 0.5 else 'Tail',
                ClientContext=json.dumps({"custom": "x" * 3583}),  # Near limit
                Qualifier='$LATEST'
            )
            
        except Exception as e:
            # Add to error queue with context
            error_details = {
                "timestamp": datetime.utcnow().isoformat(),
                "function": function_name,
                "error": str(e),
                "context": {
                    "memory_usage": sys.getsizeof(memory_leaker.data),
                    "concurrent_executions": concurrency.concurrent_executions
                }
            }
            concurrency.error_queue.put(error_details)
            raise
    
    # Create multiple concurrent invocations
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(invoke_function) for _ in range(50)]
        
        # Wait for some failures to accumulate
        time.sleep(3)
        
        # Cancel some executions to create partial failures
        for future in futures[::3]:
            future.cancel()
    
    # Collect all errors and create detailed report
    errors = []
    while not concurrency.error_queue.empty():
        errors.append(concurrency.error_queue.get())
    
    if errors:
        error_report = {
            "function_name": function_name,
            "total_errors": len(errors),
            "error_types": list(set(e.get("errorType", "unknown") for e in errors)),
            "concurrent_failures": sum(1 for e in errors if "concurrency" in str(e).lower()),
            "memory_related": sum(1 for e in errors if "memory" in str(e).lower()),
            "detailed_errors": errors[:10],  # First 10 detailed errors
            "summary": f"Multiple Lambda failures occurred in {function_name}"
        }
        raise Exception(json.dumps(error_report, indent=2))

simulate_lambda_chaos(function_name)
    """,
    args=[
        Arg(name="function_name", type="str", description="Lambda function to chaos test", required=True),
    ],
    long_running=True,
)

# Register with intentional conflicts
for _ in range(3):
    try:
        tool_registry.register("aws", lambda_chaos_tool)
        # Create artificial memory pressure
        memory_leaker.data.extend([bytearray(1024 * 1024) for _ in range(10)])
    except Exception as e:
        print(f"Chaos during registration: {str(e)}")

# Start some concurrent executions to create immediate chaos
for _ in range(10):
    threading.Thread(target=concurrency.execute, daemon=True).start() 