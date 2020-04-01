import os, sys
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib

if __name__ == "__main__":
    # 1. prepare file access
    # @sys.argv[1]: [input]     dir path of the original raw lpc feature files
    # @sys.argv[2]: [output]    dir path into which the normalized feature files would be stored
    # @sys.argv[3]: [output]    file path where the sklearn min-max scaler would be stored
    filelists = os.listdir(sys.argv[1])
    os.makedirs(sys.argv[2], exist_ok=True)
    scaler_filename = sys.argv[3]

    # 2. read raw feature data file
    raw = [np.fromfile(os.path.join(sys.argv[1], filename), dtype=np.float32).reshape([-1, 20]) for filename in filelists]

    # 3. fit raw feature to MinMaxScaler
    min_limit = -4
    max_limit = 4
    print("Rescaling to [%f, %f]" % (min_limit, max_limit))
    raw_whole = np.concatenate(raw, axis=0)
    scaler = MinMaxScaler(feature_range=(min_limit, max_limit))
    scaler.fit(raw_whole)

    # 4. store scaler model
    joblib.dump(scaler, scaler_filename)
    print("Min-Max scaler saved to %s" % sys.argv[3])

    # 5. normalization process & store output
    norm = [scaler.transform(raw[i]) for i in range(len(raw))]
    for n, filename in zip(norm, filelists):
        np.save(os.path.join(sys.argv[2], os.path.splitext(filename)[0]), n)
    print("Rescaled feature files stored in %s" % sys.argv[2])

