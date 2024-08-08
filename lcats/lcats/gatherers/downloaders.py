"""Data gathering utility functions."""
import json
import os
import requests
import shutil


LICENSE = "LICENSE"


def load_page(url, timeout=10):
    """Load a page from a URL and return the text content."""
    response = requests.get(url, timeout=timeout)
    if response.status_code == 200:
        print("File successfully downloaded.")
        return response.text
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")
        return None


class DataGatherer:
    """Utility class to download data files if needed to a given directory."""

    def __init__(self,
                 name,
                 description=None,
                 root="data",
                 suffix=".json",
                 license=None):
        """Initialize the gatherer with a name, description, and root directory.
        
        Args:
            name: The name of the gatherer.
            description: A description of the gatherer.
            root: The root directory where the data will be stored.
            suffix: The file extension to use for the data files.
        """
        self.name = name
        self.description = description
        self.root = root
        self.suffix = suffix
        self.license = license
        self.downloads = {}
    
    @property
    def path(self):
        """Return the full path to the gatherer's directory."""
        return os.path.join(self.root, self.name)

    def ensure(self, filename):
        """Ensure the directory tree exists and whether the file is there."""
        # Create the root directory if it doesn't exist
        if not os.path.exists(self.root):
            os.makedirs(self.root)

        # Create the subdirectory if provided and doesn't exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # Create the license file if it doesn't exist
        license_path = os.path.join(self.path, LICENSE)
        if not os.path.exists(license_path):
            with open(license_path, 'w', encoding='utf-8') as license_file:
                license_file.write(
                    self.license if self.license else "No license provided.")

        # Check if the file exists
        file_path = os.path.join(self.path, filename + self.suffix)
        return os.path.exists(file_path), file_path

    def download(self, filename, callback, force=False):
        """If a file doesn't already exist, download it using the callback."""
        file_exists, file_path = self.ensure(filename)

        if not file_exists or force:
            # Execute the callback to get the data to save
            descriptive_name, body_text, additional_data = callback()

            # Structure the data into a dictionary
            data_to_save = {
                "name": descriptive_name,
                "body": body_text,
                "metadata": additional_data
            }

            # Write data to JSON file
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data_to_save, json_file, indent=4)
            print(f"File {file_path} saved")
            self.downloads[filename] = file_path
        else:
            print(f"File {file_path} exists, skipping download.")

    def clear(self):
        """Clear the contents of the gatherer's directory."""
        if os.path.exists(self.path):
            # Remove all contents of the directory
            for filename in os.listdir(self.path):
                file_path = os.path.join(self.path, filename)
                try:
                    if os.path.isfile(self.path) or os.path.islink(self.path):
                        os.unlink(file_path)  # Remove the file or link
                    elif os.path.isdir(self.path):
                        shutil.rmtree(self.path)  # Remove the directory
                except Exception as e:
                    print(f'Failed to delete {self.path}. Reason: {e}')
            print(f"Cleared all contents in {self.path}")
        else:
            print(f"Directory {self.path} does not exist, nothing to clear.")
