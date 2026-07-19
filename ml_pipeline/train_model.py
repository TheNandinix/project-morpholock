import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib, os, logging, glob
from signal_processor import extract_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_csv_safely(path):
    """
    Loads one CSV of raw sensor readings, regardless of whether it
    has a text header row or not (different recording sessions may
    have been saved by different scripts). Automatically detects
    and removes a header row only if one is actually present.
    """
    df = pd.read_csv(path, header=None)
    try:
        df = df.astype(float)
    except ValueError:
        # First row wasn't numeric — it's a real header row. Drop it.
        df = df.iloc[1:].astype(float)
    return df.values.tolist()


def train(csv_folder, output_path):
    files = glob.glob(os.path.join(csv_folder, '*.csv'))
    logger.info(f'Found {len(files)} CSV files')
    features = []
    skipped = 0
    for f in files:
        try:
            data = load_csv_safely(f)
            feat = extract_features(data)
            if feat is not None:
                features.append(feat)
            else:
                skipped += 1
                print(f'SKIPPED {f}: extract_features returned None (not enough rows)')
        except Exception as e:
            skipped += 1
            print(f'SKIPPED {f}: {e}')

    logger.info(f'Successfully processed {len(features)} files, skipped {skipped}')
    X = np.array(features)
    logger.info(f'Training on {len(X)} sequences')

    if len(X) < 10:
        raise RuntimeError(
            f"Only {len(X)} usable sequences found — need at least a "
            f"handful to train. Check the SKIPPED messages above for why "
            f"files were rejected."
        )

    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f'Model saved to {output_path}')
    return model


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    csv_folder = os.path.join(project_root, 'training_data')
    output_path = os.path.join(project_root, 'models', 'morpholock_model.pkl')
    train(csv_folder, output_path)