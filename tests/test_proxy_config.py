"""Static guards for the standard Compose proxy configuration.

Run with: python -m unittest discover -s tests -p test_proxy_config.py -v
These checks need no database or Docker; they do not replace nginx -t or
docker compose config validation.
"""

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class StandardComposeProxyTests(unittest.TestCase):
    def test_nginx_overwrites_forwarded_for_with_peer_address(self):
        config = (PROJECT_ROOT / "frontend/nginx.conf").read_text(encoding="utf-8")
        api_location = re.search(r"location /api/\s*\{([^{}]*)\}", config)
        self.assertIsNotNone(api_location, "Expected the API proxy location")
        forwarded_for = re.findall(
            r"(?im)^\s*proxy_set_header\s+X-Forwarded-For\s+([^;]+);",
            api_location.group(1),
        )
        self.assertEqual(forwarded_for, ["$remote_addr"])
        self.assertNotIn("$http_x_forwarded_for", config)

    def test_backend_has_no_published_port_or_host_network(self):
        config = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        # Match the backend block in this project's block-style Compose file.
        backend = re.search(
            r"(?ms)^  backend:[ \t]*\n(.*?)(?=^  \S|\Z)", config
        )
        self.assertIsNotNone(backend, "Expected the backend service")
        self.assertNotRegex(backend.group(1), r"(?m)^    (ports|network_mode):")


if __name__ == "__main__":
    unittest.main()
