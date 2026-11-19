set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "cbee11a6|24a9e61c" && { echo "MY JOB QUEUED/RUNNING; stop"; exit 1; }
test -d $X/s24k && test ! -e $X/a24k
cd $X/s24k && sha256sum -c - <<"EOS" 2>&1 | grep -v ": OK$" | head -3; echo S24K_CHECKED $(find . -type f | wc -l)
0f5c7062223015834ab2bfafc8e5370628932809fc986fb9ffba07499f603ff2  n/BUILD.json
814db98aabae2859b8be5bc8e509cc8fd43bd9baa32c11ec293176f155b116f8  n/SHA256SUMS.txt
9c34fb06deac469992e4aa405d9b59f66fe9bee73ab2c1c67b51623ae0f3c731  n/b/a.py
b34eeb2bd0c5db05d2ed2056369f2838211d8a7b5134e59fb7b8d9080d5e2341  n/b/f.sh
8d9fcaa12efd038debd78853ab6eae0fbccb0f15c843fe4b7241d28c1cc60949  n/b/gc.py
818e86b83da146b3076ed8dea9d8497a51acf76d24afeb015e978d038d970d2c  n/b/h.py
f02e8848bf601d63538488ee13b0d102a8d5d6a3519097ae6db7bdfcf98672bd  n/b/i.py
c78e969dd37fef3684275a64b4bc0638c139fcfec003c93abf16d89321cb90cd  n/b/o.py
4adfa8ab8eee48ea318e1f9dae225f892c8dcfbd486554d8453e0a8ef0dbd6d4  n/b/pc.py
4cb9f8df31574615bc9ac43a08924ba66a86673ba9e152e34d472dd3cc73bf03  n/b/pc.sh
3062e071b5137ff831241a16d77d743457fc1e9e30efe78f31505081cab0a464  n/b/pl.py
489f55dc1c8a6462b2bbc3cd3b4fc29911faa23f12a212765608826d04d20fd4  n/b/rg.py
92e12efb6172841ab6c413da0785a42ac4950f701f49c4f317c9a676e9e9dbc9  n/b/rv.py
3f690c58d1da3653f72a49e3396c2c9bdf51b6f6b4ba9b639abcc392d9915a9c  n/b/sr.py
77bf6769caaecb459f876cd8696f9c01fcfed0d66a1eb4e8b0b806be9d04618b  n/b/u.py
f999c5d51673e6999c2658e93dabd8f720315c4598b16f5bbdfbd24b8f2dea58  n/b/z.py
5d1a50004e298cb32076af6a5eccf5c2528d0680544fe8f7412551811005ad55  n/job.sh
317a8c11c7fc0af7a2b590d9b8667f86430e5f56d3b964e845481a54c4dfb811  n/k/7.json
a2edff8d34f1168396c6799f3e422ce3e9b1e2c0c3a4ffd889467350177505f5  n/k/a.json
08cc9f8a46e9ae34ff3716eb7579d3845fa3b52f711b37bf898d90cf03aecb7c  n/k/c.json
b8e5e925efb2390df0957d5fca148f8822f9e893daa2743e9fe436038ec7d897  n/k/c0.json
290eef6161712d86319fada51e33052ca8d4c6fcc43edb8065c666aa7f557268  n/k/h.json
61199e8f52b92c3bf1676dd98451fbf4eca694d34e9d5a8a8140a248332a83aa  n/k/j.json
2ad4032d5927800d0eafb6c96d33b1d268b9bd4e2c1c9d719a70c99f56363aee  n/k/n.json
fd4d0fbc80ad5e720a6df9233ade750059aa1c6d36756373232850704c650261  n/k/p.json
1f0b53cda0ccc4b39e33363ced11597e6d795214843b8f2b2a8e49f9794a5ab0  n/k/r.json
f23da69630b038cfe89682f4e320449812b432a3e033a222adae04eb2706e04d  n/k/t_e047002134f979bd.tar
fe63459826d83b49bafddba41d25640e52ef2a188f78f3837b2a80047f2d9692  n/k/y.json
3c6ed2a5044c6024516c41d2d230c3f30c5b9a71a51053ad7eb1803b13cf5769  q/BUILD.json
6215397d48349983ef30c5b7492618d570f4586d0c85f9d101e00c7bb96669c3  q/SHA256SUMS.txt
5935b4e0e7f65f1a8a59ababfa3ad44ab6182cefee4271c15bdc12ee449e3c05  q/b/a.py
b34eeb2bd0c5db05d2ed2056369f2838211d8a7b5134e59fb7b8d9080d5e2341  q/b/f.sh
f02e8848bf601d63538488ee13b0d102a8d5d6a3519097ae6db7bdfcf98672bd  q/b/i.py
0c0c49ce456f65a35ba2710acbbe213e54395d523e975a8a8315be703ae815bb  q/b/o.py
3062e071b5137ff831241a16d77d743457fc1e9e30efe78f31505081cab0a464  q/b/pl.py
489f55dc1c8a6462b2bbc3cd3b4fc29911faa23f12a212765608826d04d20fd4  q/b/rg.py
f999c5d51673e6999c2658e93dabd8f720315c4598b16f5bbdfbd24b8f2dea58  q/b/z.py
80040cb7ab58e3d8a9229972d73ab31db2e2bae7fd674634c7af6414742ffb30  q/job.sh
317a8c11c7fc0af7a2b590d9b8667f86430e5f56d3b964e845481a54c4dfb811  q/k/7.json
dcfd292264d372c50ddc52cbc0fb0dbe0397bc80afa91b66535c83be41f70df5  q/k/a.json
b8025fd5a57305a9a53e148575405a82200e728106a29667b7fbc72bf60bc6af  q/k/c.json
b8e5e925efb2390df0957d5fca148f8822f9e893daa2743e9fe436038ec7d897  q/k/c0.json
290eef6161712d86319fada51e33052ca8d4c6fcc43edb8065c666aa7f557268  q/k/h.json
cf5429a784008fb51e3214d61d0c0929f4854982b9cad5e2396daeda18fd428d  q/k/j.json
5ed88bd0bcc11038d33028e4d4f025ff6a3f02e4780733e0d1980dc464480f5f  q/k/n.json
fd4d0fbc80ad5e720a6df9233ade750059aa1c6d36756373232850704c650261  q/k/p.json
1f0b53cda0ccc4b39e33363ced11597e6d795214843b8f2b2a8e49f9794a5ab0  q/k/r.json
f23da69630b038cfe89682f4e320449812b432a3e033a222adae04eb2706e04d  q/k/t_e047002134f979bd.tar
0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad  u/0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad
34916a84e82e61e9c8cf9bafa6a7f78e0ab18b4f4986ee07e76df930aee6276a  u/34916a84e82e61e9c8cf9bafa6a7f78e0ab18b4f4986ee07e76df930aee6276a
773ba292e5ed0d8c5720a6bed8261a3f8b21230598897d9e0f02fda01784e679  u/773ba292e5ed0d8c5720a6bed8261a3f8b21230598897d9e0f02fda01784e679
bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3  u/bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3
EOS
mkdir -m 700 $X/a24k
for K in q n; do cd $X/s24k/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24k/over_$K/$(dirname $f); mv $X/$K/$f $X/a24k/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for f in $(cd $X/s24k && find u -type f); do if [ -e $X/$f ]; then cmp -s $X/s24k/$f $X/$f || { echo "DIFFERS $f"; exit 1; }; else mv $X/s24k/$f $X/$f; fi; done
for K in q n; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24k/extra_$K/$(dirname $f); mv $f $X/a24k/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK$" | head -5; done
