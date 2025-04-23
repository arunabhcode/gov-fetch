import os
import sys
from pathlib import Path
from dotenv import load_dotenv


class EnvLoader:
    """Handles finding the project root and loading the .env file."""

    @staticmethod
    def find_repo_root(start_path: str | Path | None = None) -> Path | None:
        """
        Finds the root directory of the git repository.
        """
        if start_path is None:
            # Try to get the caller's file path
            try:
                # stack()[1] gives the frame of the caller
                caller_frame = sys._getframe(1)
                start_path = Path(caller_frame.f_globals["__file__"]).parent
            except (AttributeError, KeyError, IndexError):
                # Fallback to current working directory if caller info is unavailable
                start_path = Path.cwd()
        else:
            start_path = Path(start_path)

        current_path = start_path.resolve()

        while True:
            if (current_path / ".git").is_dir():
                return current_path
            parent_path = current_path.parent
            if parent_path == current_path:
                # Reached the filesystem root
                return None
            current_path = parent_path

    @staticmethod
    def load_dotenv(root_path: Path | None = None) -> bool:
        """
        Loads environment variables from the .env file in the repository root.
        """
        if root_path is None:
            root_path = EnvLoader.find_repo_root()

        if root_path is None:
            print("Warning: Repository root not found. Cannot load .env file.")
            return False

        env_path = root_path / ".env"

        if not env_path.is_file():
            print(f"Warning: .env file not found at {env_path}")
            return False

        loaded = load_dotenv(dotenv_path=env_path, override=True)
        if loaded:
            print(f"Loaded environment variables from: {env_path}")
        else:
            # This might happen if the file is empty or only contains comments
            print(f"Found .env file at {env_path}, but no variables were loaded.")

    @staticmethod
    def check_env_variables():
        """
        Checks if critical environment variables are loaded.
        Raises ValueError if Mailgun keys are missing.
        Prints a warning if recipient emails are missing.
        """
        mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        recipient_emails = os.getenv("RECIPIENT_EMAILS")
        if not mailgun_api_key or not mailgun_domain:
            raise ValueError(
                "Error: MAILGUN_API_KEY and MAILGUN_DOMAIN environment variables must be set."
            )

        # Check if recipient_emails is set and not empty after splitting
        # Handles cases like RECIPIENT_EMAILS="" or RECIPIENT_EMAILS=",,"
        if not recipient_emails or not any(
            email.strip() for email in recipient_emails.split(",")
        ):
            raise ValueError(
                "Error: RECIPIENT_EMAILS environment variable is not set or empty. Mail agent will not send emails."
            )

        return True

    @staticmethod
    def load_and_check():
        """
        Loads the .env file and then checks for required variables.
        Combines load_dotenv and check_env_variables.
        Raises ValueError if critical variables are missing after loading.
        """
        EnvLoader.load_dotenv()
        # Check is performed even if .env wasn't found or loaded,
        # as variables might be set in the actual environment.
        return EnvLoader.check_env_variables()


# Example Usage (for testing purposes)
if __name__ == "__main__":
    repo_root = EnvLoader.find_repo_root()
    if repo_root:
        print(f"Repository root found: {repo_root}")
        EnvLoader.load_dotenv(root_path=repo_root)
        # Example: Access an environment variable
        # test_var = os.getenv("TEST_VARIABLE")
        # if test_var:
        #     print(f"TEST_VARIABLE: {test_var}")
        # else:
        #     print("TEST_VARIABLE not found in .env or environment.")
    else:
        print("Repository root not found.")
