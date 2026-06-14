import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib, os, logging, glob
from signal_processor import extract_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train(csv_folder, output_path):
    files = glob.glob(os.path.join(csv_folder, '*.csv'))
    logger.info(f'Found {len(files)} CSV files')

    features = []
    for f in files:
        try:
            df = pd.read_csv(f, header=0)
            data = df.values.tolist()
            feat = extract_features(data)
            if feat is not None:
                features.append(feat)
        except Exception as e:
            logger.warning(f'Skipped {f}: {e}')

    X = np.array(features)
    logger.info(f'Training on {len(X)} sequences')

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42)
    model.fit(X)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f'Model saved to {output_path}')
    return model


if __name__ == '__main__':
    train(
        csv_folder='data/raw_recordings',
        output_path='models/morpholock_model.pkl'
    )