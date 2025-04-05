import os
import configparser

def debug_print_aws_config_sections():
    """Print all sections from ~/.aws/config to debug what we are seeing."""
    config_path = os.path.expanduser("~/.aws/config")
    config = configparser.ConfigParser()
    config.read(config_path)

    print(f"\n📄 Reading config file: {config_path}\n")
    print("✅ Sections detected:")

    if not config.sections():
        print("❌ No sections found in ~/.aws/config! (Check the file path or content)")
        return

    for section in config.sections():
        print(f"  - {section}")

if __name__ == "__main__":
    debug_print_aws_config_sections()
