from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ml.retrain import ModelRetrainer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def train_model_for_user(request):
    user = request.user
    
    if not user or not user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)
    
    apps = request.data.get("apps", [])

    if not apps:
        return Response({"error": "No apps sent"}, status=400)
    
    model, metrics = ModelRetrainer.train_model(user, apps=apps)

    if model is None:
        return Response({"error": "Not enough data to train"}, status=400)

    return Response({
        "status": "trained",
        "metrics": metrics
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retrain_model(request):
    user = request.user

    # Step 1 — check if retrain is needed
    should_train, reason = ModelRetrainer.should_retrain(user)

    if not should_train:
        return Response({
            "status": "skipped",
            "reason": reason
        }, status=200)

    # Step 2 — train model
    model, metrics = ModelRetrainer.train_model(user)

    if model is None:
        return Response({
            "status": "failed",
            "error": "Not enough data or training failed"
        }, status=400)

    # Step 3 — return success
    return Response({
        "status": "retrained",
        "reason": reason,
        "metrics": metrics
    }, status=200)
