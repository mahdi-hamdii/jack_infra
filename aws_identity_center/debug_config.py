import os
import configparser

def list_profiles_debug():
    """List AWS profiles from ~/.aws/config more safely."""
    config_path = os.path.expanduser("~/.aws/config")
    config = configparser.ConfigParser()
    config.read(config_path)

    profiles = []

    print(f"\n✅ Sections detected:")
    for section in config.sections():
        print(f"  - {section}")

        # Safely detect if it's a profile
        if section.lower().strip().startswith("profile "):
            profile_name = section.strip().split("profile ", 1)[-1].strip()
            profiles.append(profile_name)

    if not profiles:
        print("\n❌ No profiles detected based on section names. Please check your file format carefully!")
    else:
        print("\n✅ Profiles extracted:")
        for profile in profiles:
            print(f"  - {profile}")

    return profiles

if __name__ == "__main__":
    list_profiles_debug()
