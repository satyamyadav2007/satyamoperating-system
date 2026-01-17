import datetime
# Try to import Sandbox. If it fails (user didn't install it), we handle it gracefully.
try:
    from e2b_code_interpreter import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False

class AgentTools:
    """
    These are the actual functions the Agent OS can execute.
    In the 'AWS for Agents' model, these are your 'Services'.
    """

    @staticmethod
    def read_emails():
        """Simulates reading emails from an inbox."""
        # In a real app, use the Gmail API here
        return [
            {"from": "boss@work.com", "subject": "Urgent Report", "body": "Need the Q1 stats now."},
            {"from": "newsletter@tech.com", "subject": "AI News", "body": "Agents are taking over!"}
        ]

    @staticmethod
    def get_system_time():
        """Returns the current server time."""
        return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}"

    @staticmethod
    def execute_python(code: str):
        """Runs Python code in a secure, isolated cloud environment."""
        
        # Fallback if E2B is not installed or configured
        if not E2B_AVAILABLE:
            return "ERROR: 'e2b-code-interpreter' is not installed. Please install it to run Python code safely."

        try:
            # This happens on a remote secure server, NOT your laptop
            # You need an E2B_API_KEY in your environment variables for this to work
            with Sandbox() as sb:
                execution = sb.run_code(code)
                
                if execution.error:
                    return f"Runtime Error: {execution.error.name}: {execution.error.value}"
                
                # combine stdout and results
                output = []
                if execution.logs.stdout:
                    output.append(str(execution.logs.stdout))
                if execution.results:
                    output.append(str(execution.results))
                    
                return "\n".join(output) if output else "Code executed successfully (No output)"
                
        except Exception as e:
            return f"Sandbox Error: {str(e)}"