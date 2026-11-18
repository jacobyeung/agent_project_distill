R=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/inputs
P=$R/prepare_9b0c4b095487492a80bd5e9030d5bbc0
cd $R && tar czf - data_receipt.json prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json prepare_9b0c4b095487492a80bd5e9030d5bbc0/vqa/receipt.json prepare_9b0c4b095487492a80bd5e9030d5bbc0/routing/receipt.json prepare_9b0c4b095487492a80bd5e9030d5bbc0/pointing/receipt.json prepare_9b0c4b095487492a80bd5e9030d5bbc0/result.json | base64 -w0
