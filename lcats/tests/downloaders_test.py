"""Tests for the downloaders module."""

import os
import unittest
from unittest.mock import patch, Mock

# import parameterized
import requests


from lcats import constants
from lcats import test_utils
from lcats.gatherers import downloaders


class TestLoadPage(unittest.TestCase):
    """Tests for the load_page function."""

    @patch('lcats.gatherers.downloaders.requests.get')
    def test_load_page_success(self, mock_get):
        """Test the load_page function with a successful response."""
        # Create a mock response object with the desired properties
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mocked page content"
        mock_get.return_value = mock_response
        
        # Call the function
        result = downloaders.load_page("http://example.com")
        
        # Assert the expected behavior
        self.assertEqual(result, "Mocked page content")
        mock_get.assert_called_once_with("http://example.com", timeout=10)

    @patch('lcats.gatherers.downloaders.requests.get')
    def test_load_page_failure(self, mock_get):
        """Test the load_page function with a failed response."""
        # Create a mock response object with a failure status code
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        # Call the function
        result = downloaders.load_page("http://example.com")
        
        # Assert the expected behavior
        self.assertIsNone(result)
        mock_get.assert_called_once_with("http://example.com", timeout=10)

    @patch('lcats.gatherers.downloaders.requests.get')
    def test_load_page_timeout(self, mock_get):
        """Test the load_page function with a timeout exception."""
        # Simulate a timeout exception
        mock_get.side_effect = requests.exceptions.Timeout
        
        # Call the function
        with self.assertRaises(requests.exceptions.Timeout):
            downloaders.load_page("http://example.com")


class TestFilenameFromUrl(unittest.TestCase):
    """Tests for the filename_from_url function."""

    def test_basic_url(self):
        """Test generating a filename from a basic URL."""
        url = "http://example.com/file.txt"
        expected_extension = ".txt"
        filename = downloaders.filename_from_url(url)
        
        # Ensure the filename ends with the correct extension
        self.assertTrue(filename.endswith(expected_extension))
        
        # Ensure the filename is correctly hashed and unique
        self.assertEqual(len(filename), 64 + len(expected_extension))
    
    def test_url_with_query(self):
        """Test generating a filename from a URL with a query parameter."""
        url = "http://example.com/file.txt?param=value"
        filename = downloaders.filename_from_url(url)
        
        # Ensure the filename is unique even with a query parameter
        self.assertEqual(len(filename), 64 + 4)  # 64 for the hash + 4 for ".txt"
    
    def test_url_without_extension(self):
        """Test generating a filename from a URL without an extension."""
        url = "http://example.com/file"
        filename = downloaders.filename_from_url(url)
        
        # Ensure the filename has no extension
        self.assertEqual(len(filename), 64)
        self.assertTrue('.' not in filename)
    
    def test_url_with_no_path(self):
        """Test generating a filename from a URL with no path."""
        url = "http://example.com"
        filename = downloaders.filename_from_url(url)
        
        # Ensure the filename has no extension and is hashed correctly
        self.assertEqual(len(filename), 64)
    
    def test_empty_url(self):
        """Test generating a filename from an empty URL."""
        url = ""
        filename = downloaders.filename_from_url(url)
        
        # Ensure the filename is still a valid hash with no extension
        self.assertEqual(len(filename), 64)


class TestLambdaResourceCache(test_utils.TestCaseWithData):

    def test_instantiation(self):
        """Test instantiating a LocalTreeReader with no parameters."""
        try:
            cache = downloaders.LambdaResourceCache(
                canonicalizer=lambda x: x,
                acquirer=lambda x: x
            )
            self.assertIsInstance(
                cache, downloaders.LambdaResourceCache,
                "LambdaResourceCache instance was not created correctly.") 
            self.assertEqual(cache.root, constants.CACHE_ROOT)
        except Exception as e:
            self.fail(f"Instantiation of LambdaResourceCache failed: {e}")

    def test_instantiation_with_root(self):
        """Test instantiating a LocalTreeReader with a root parameter."""
        try:
            cache = downloaders.LambdaResourceCache(
                canonicalizer=lambda x: x,
                acquirer=lambda x: x,
                root=self.test_temp_dir
            )
            self.assertIsInstance(
                cache, downloaders.LambdaResourceCache,
                "LambdaResourceCache instance was not created correctly.")
            self.assertEqual(cache.root, self.test_temp_dir)
        except Exception as e:
            self.fail(f"Instantiation of LambdaResourceCache failed: {e}")  

    def test_full_path(self):
        """Test the full_path method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x
        )
        self.assertEqual(
            cache.full_path("foo.bar"),
            os.path.join(constants.CACHE_ROOT, "foo.bar"),
            "Full path failed."
        )

    def test_ensure(self):
        """Test the ensure method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x
        )
        
        full_path = cache.full_path("foo.bar")
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file or link
        file_exists, path = cache.ensure("foo.bar")
        self.assertFalse(file_exists, "File should not exist.")
        self.assertEqual(path, full_path, "Path is correct.")

        with open(full_path, 'w', encoding=constants.TEXT_ENCODING) as file:
            file.write("contents")
        file_exists, path = cache.ensure("foo.bar")
        self.assertTrue(file_exists, "File should exist.")
        self.assertEqual(path, full_path, "Path is correct.")
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file or link

    def test_canonicalize(self):
        """Test the canonicalize method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x
        )
        self.assertEqual(
            cache.canonicalize("foo.bar"),
            "foo.bar",
            "Canonicalization failed."
        )

    def test_acquire(self):
        """Test the acquire method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x
        )
        self.assertEqual(
            cache.acquire("foo.bar"),
            "foo.bar",
            "Acquisition failed."
        )

    def test_store_with_root(self):
        """Test the store method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x,
            root=self.test_temp_dir
        )
        canonical = cache.canonicalize("foo.bar")
        full_path = cache.full_path(canonical)
        contents = "contents"
        cache.store(contents, full_path)
        self.assertTrue(
            os.path.exists(full_path),
            "Store failed to write a file."
        )
        with open(full_path, 'r', encoding=constants.TEXT_ENCODING) as file:
            self.assertEqual(
                file.read(),
                contents,
                "Contents of stored file are incorrect."
            )

    def test_cache(self):
        """Test the cache method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x,
            root=self.test_temp_dir
        )
        resource = "foo.bar"
        full_path = cache.cache(resource)
        self.assertTrue(
            os.path.exists(full_path),
            "Cache failed to write a file."
        )
        with open(full_path, 'r', encoding=constants.TEXT_ENCODING) as file:
            self.assertEqual(
                file.read(),
                resource,
                "Contents of stored file are incorrect."
            )
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file or link

    def test_get(self):
        """Test the get method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x,
            root=self.test_temp_dir
        )
        resource = "foo.bar"
        full_path = cache.cache(resource)
        self.assertEqual(
            cache.get(resource),
            resource,
            "Get failed to return the correct contents."
        )
        self.assertTrue(
            os.path.exists(full_path),
            "Get failed to write a file."
        )
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file or link

    def test_clear(self):
        """Test the clear method."""
        cache = downloaders.LambdaResourceCache(
            canonicalizer=lambda x: x,
            acquirer=lambda x: x,
            root=self.test_temp_dir
        )
        resource = "foo.bar"
        full_path = cache.cache(resource)
        self.assertTrue(
            os.path.exists(full_path),
            "Cache failed to write a file."
        )
        cache.clear()
        self.assertFalse(
            os.path.exists(full_path),
            "Clear failed to remove the file."
        )

class TestUrlResourceCache(test_utils.TestCaseWithData):

    def test_instantiation(self):
        """Test instantiating a LocalTreeReader with no parameters."""
        try:
            cache = downloaders.UrlResourceCache()
            self.assertIsInstance(
                cache, downloaders.UrlResourceCache,
                "UrlResourceCache instance was not created correctly.") 
            self.assertEqual(cache.root, constants.CACHE_ROOT)
        except Exception as e:
            self.fail(f"Instantiation of UrlResourceCache failed: {e}")

    def test_instantiation_with_root(self):
        """Test instantiating a LocalTreeReader with a root parameter."""
        try:
            cache = downloaders.UrlResourceCache(
                root=self.test_temp_dir
            )
            self.assertIsInstance(
                cache, downloaders.UrlResourceCache,
                "UrlResourceCache instance was not created correctly.")
            self.assertEqual(cache.root, self.test_temp_dir)
        except Exception as e:
            self.fail(f"Instantiation of UrlResourceCache failed: {e}")  

    def test_full_path(self):
        """Test the full_path method."""
        cache = downloaders.UrlResourceCache()
        self.assertEqual(
            cache.full_path("foo.bar"),
            os.path.join(constants.CACHE_ROOT, "foo.bar"),
            "Full path failed."
        )

    def test_ensure(self):
        """Test the ensure method."""
        cache = downloaders.UrlResourceCache(
            root=self.test_temp_dir
        )
        
        full_path = cache.full_path("foo.bar")
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file.
        file_exists, path = cache.ensure("foo.bar")
        self.assertFalse(file_exists, "File should not exist.")
        self.assertEqual(path, full_path, "Path is correct.")

        with open(full_path, 'w', encoding=constants.TEXT_ENCODING) as file:
            file.write("contents")
        file_exists, path = cache.ensure("foo.bar")
        self.assertTrue(file_exists, "File should exist.")
        self.assertEqual(path, full_path, "Path is correct.")
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file.

    def test_canonicalize(self):
        """Test the canonicalize method."""
        cache = downloaders.UrlResourceCache()
        self.assertEqual(
            cache.canonicalize("foo.bar"),
            downloaders.filename_from_url("foo.bar"),
            "Canonicalization failed."
        )

    @patch('lcats.gatherers.downloaders.requests.get')
    def test_acquire(self, mock_get):
        """Test the acquire method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mocked page content"
        mock_get.return_value = mock_response

        resource = "http://example.com"
        cache = downloaders.UrlResourceCache()
        self.assertEqual(
            cache.acquire(resource),
            mock_response.text,
            "Acquisition failed."
        )
        mock_get.assert_called_once_with(resource, timeout=10)

    @patch('lcats.gatherers.downloaders.requests.get')
    def test_store_with_root(self, mock_get):
        """Test the store method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mocked page content"
        mock_get.return_value = mock_response

        cache = downloaders.UrlResourceCache(
            root=self.test_temp_dir
        )
        resource = "http://example.com"
        canonical = cache.canonicalize(resource)
        full_path = cache.full_path(canonical)
        
        contents = "contents"
        cache.store(contents, full_path)
        self.assertTrue(
            os.path.exists(full_path),
            "Store failed to write a file."
        )
        with open(full_path, 'r', encoding=constants.TEXT_ENCODING) as file:
            self.assertEqual(
                file.read(),
                mock_response.text,
                "Contents of stored file are incorrect."
            )
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file

    @patch('lcats.gatherers.downloaders.requests.get')
    def test_cache(self, mock_get):
        """Test the cache method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mocked page content"
        mock_get.return_value = mock_response

        cache = downloaders.UrlResourceCache(
            root=self.test_temp_dir
        )
        resource = "http://example.com"
        full_path = cache.cache(resource)
        self.assertTrue(
            os.path.exists(full_path),
            "Cache failed to write a file."
        )
        with open(full_path, 'r', encoding=constants.TEXT_ENCODING) as file:
            self.assertEqual(
                file.read(),
                mock_response.text,
                "Contents of stored file are incorrect."
            )
        if os.path.exists(full_path):
            os.unlink(full_path)

    @patch('lcats.gatherers.downloaders.requests.get')
    def test_get(self, mock_get):
        """Test the get method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mocked page content"
        mock_get.return_value = mock_response

        cache = downloaders.UrlResourceCache(
            root=self.test_temp_dir
        )
        resource = "http://example.com"
        full_path = cache.cache(resource)
        self.assertEqual(
            cache.get(resource),
            mock_response.text,
            "Get failed to return the correct contents."
        )
        self.assertTrue(
            os.path.exists(full_path),
            "Get failed to write a file."
        )
        if os.path.exists(full_path):
            os.unlink(full_path)  # Remove the file

    def test_clear(self):
        """Test the clear method."""
        cache = downloaders.UrlResourceCache(
            root=self.test_temp_dir
        )
        resource = "http://example.com"
        full_path = cache.cache(resource)
        self.assertTrue(
            os.path.exists(full_path),
            "Cache failed to write a file."
        )
        cache.clear()
        self.assertFalse(
            os.path.exists(full_path),
            "Clear failed to remove the file."
        )

if __name__ == '__main__':
    unittest.main()
