# ml/baseline.py
from ml.model import UserNotificationModel
from ml.synthetic import SyntheticDataGenerator

def get_baseline_model():
    dataset = SyntheticDataGenerator.generate_for_cold_start(apps=None, n=500)
    model = UserNotificationModel(model_type='ridge')
    model.train(dataset, validate=False)
    return model
