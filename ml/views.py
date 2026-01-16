from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ml.retrain import ModelRetrainer
from django.http import FileResponse

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def train_model_for_user(request):
    user = request.user
    apps = request.data.get("apps", [])

    if not apps:
        return Response({"error": "No apps sent"}, status=400)

    metrics, file_path = ModelRetrainer.train_model(user, apps=apps)

    if not file_path:
        return Response({"error": "Not enough data"}, status=400)

    file = open(file_path, "rb")
    response = FileResponse(file, content_type="application/octet-stream")
    response["Content-Disposition"] = 'attachment; filename="model.onnx"'
    response["X-Delete-File"] = file_path
    return response

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retrain_model(request):
    user = request.user

    should_train, reason = ModelRetrainer.should_retrain(user)

    if not should_train:
        return Response({
            "status": "skipped",
            "reason": reason
        }, status=200)

    metrics, file_path = ModelRetrainer.train_model(user)

    if not file_path:
        return Response({
            "status": "failed",
            "error": "Not enough data or training failed"
        }, status=400)

    file = open(file_path, "rb")
    response = FileResponse(file, content_type="application/octet-stream")
    response["Content-Disposition"] = 'attachment; filename="model.onnx"'
    response["X-Delete-File"] = file_path
    return response