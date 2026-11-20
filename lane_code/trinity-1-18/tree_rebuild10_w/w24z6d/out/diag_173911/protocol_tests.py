import importlib.util,sys,os,json,unittest,hashlib,base64,runpy
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from strict_sink import Connection
class Protocol(unittest.TestCase):
 def setUp(self):
  root=HERE/"protocol_cases"/self._testMethodName;root.mkdir(parents=True)
  os.environ["STRICT_SINK"]=str(root);os.environ["REQUIRE_RANGE"]="0";os.environ.pop("SINK_FAILURE",None)
 def request(self,data=b"q",cr=None,name="object",length=None):
  c=Connection("local.invalid");c.putrequest("PUT","/"+name)
  c.putheader("Content-Length",len(data) if length is None else length);c.putheader("Content-Type","application/octet-stream")
  if cr is not None:c.putheader("Content-Range",cr)
  c.endheaders();c.send(data);return c.getresponse()
 def test_single_request_without_range(self):
  r=self.request(b"q"*71);self.assertEqual(r.status,200);m=json.loads(r.read());self.assertEqual(m["size"],"71");self.assertEqual(m["md5Hash"],base64.b64encode(hashlib.md5(b"q"*71).digest()).decode())
 def test_explicit_final_small(self):self.assertEqual(self.request(b"qq", "bytes 0-1/2").status,200)
 def test_chunks_308_range_final(self):
  r=self.request(b"q"*(256*1024),"bytes 0-262143/262145");self.assertEqual(r.status,308);self.assertEqual(r.getheader("Range"),"bytes=0-262143")
  r=self.request(b"q","bytes 262144-262144/262145");self.assertEqual(r.status,200)
 def test_status_probe_and_consumed_session(self):
  self.assertEqual(self.request(b"","bytes */*").status,308)
  self.assertEqual(self.request().status,200)
  self.assertEqual(self.request(b"","bytes */1").status,200)
  self.assertEqual(self.request().status,410)
 def test_bad_chunk_alignment(self):self.assertEqual(self.request(b"qq","bytes 0-1/*").status,400)
 def test_bad_length(self):self.assertEqual(self.request(b"qq",length=3).status,400)
 def test_bad_offset(self):self.assertEqual(self.request(b"qq","bytes 1-2/3").status,400)
 def test_bad_range_length(self):self.assertEqual(self.request(b"qq","bytes 0-2/3").status,400)
 def test_changed_total(self):
  self.assertEqual(self.request(b"q"*262144,"bytes 0-262143/262146").status,308)
  self.assertEqual(self.request(b"q","bytes 262144-262144/262145").status,400)
 def test_create_only_conflict(self):
  os.environ["SINK_FAILURE"]="precondition";self.assertEqual(self.request().status,412)
 def test_crc32c_reference(self):
  from strict_sink import crc32c
  self.assertEqual(crc32c(b"123456789"),"4waSgw==")
 def test_writer_rejects_bad_metadata(self):
  os.environ["SINK_FAILURE"]="bad_md5"
  g=runpy.run_path(str(HERE.parent/"kit_n/b/gc.py"),run_name="test_gc")
  import http.client
  old=http.client.HTTPSConnection;http.client.HTTPSConnection=Connection
  p=Path(os.environ["STRICT_SINK"])/"payload";p.write_bytes(b"hello")
  try:
   with self.assertRaisesRegex(OSError,"size/md5 mismatch"):g["upload"]("https://local.invalid/object",p,0,5,"object")
  finally:http.client.HTTPSConnection=old
if __name__=="__main__":unittest.main(verbosity=2)
