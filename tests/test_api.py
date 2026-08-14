import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.client = TestClient(app)

    def test_public_indicator_has_no_personal_pic(self):
        body = self.client.get("/api/v1/indikator?page_size=1").json()["data"][0]
        self.assertNotIn("nama_pic", body)
        self.assertNotIn("pic_provinsi", body)
        self.assertNotIn("status_ketersediaan", body)

    def test_availability_endpoints_are_removed(self):
        for path in ("/api/v1/ringkasan", "/api/v1/matriks-ketersediaan", "/api/v1/indikator-rawan", "/api/v1/tim-pjk"):
            self.assertEqual(self.client.get(path).status_code, 404)
