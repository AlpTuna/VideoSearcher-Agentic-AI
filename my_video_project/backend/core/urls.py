from django.contrib import admin
from django.urls import path
from core.views import ffmpeg1_view, DeepSpeechView, ffmpeg2_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ffmpeg1/', ffmpeg1_view.as_view()),
    path('deepspeech/', DeepSpeechView.as_view()),
    path('ffmpeg2/', ffmpeg2_view.as_view()),
]