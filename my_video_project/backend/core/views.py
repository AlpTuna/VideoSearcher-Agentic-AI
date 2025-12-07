# backend/core/views.py
import docker
import os
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Initialize Docker client
client = docker.from_env()

@method_decorator(csrf_exempt, name='dispatch')
class ffmpeg1_view(View):
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)

        uploaded_file = request.FILES['file']
        
        # 1. Save file to Shared Volume (/data/uploads)
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(uploaded_file.name, uploaded_file)
        
        # Determine paths as seen by the containers
        # Both containers see the volume mounted at /data
        input_path = f"/data/uploads/{filename}"
        
        # We'll create a folder for outputs based on the filename
        output_folder = f"/data/outputs/{os.path.splitext(filename)[0]}"
        output_prefix = f"{output_folder}/clip"
        
        # Ensure output directory exists (Django can do this because it shares the volume)
        os.makedirs(output_folder, exist_ok=True)

        # 2. Command the Worker
        # We look up the container by the name defined in docker-compose.yml
        #worker_name = os.environ.get('WORKER_NAME', 'worker_ffmpeg1')
        worker_name = 'worker_ffmpeg1'

        try:
            container = client.containers.get(worker_name)
            
            # The command we run inside the worker container
            cmd = f"python main.py -i {input_path} -o {output_prefix}"
            
            # Execute and wait for result
            exec_result = container.exec_run(cmd)
            
            if exec_result.exit_code == 0:
                return JsonResponse({
                    "status": "success", 
                    "message": f"Successfuly split {filename}",
                    "output_location": output_folder
                })
            else:
                return JsonResponse({
                    "status": "error", 
                    "logs": exec_result.output.decode('utf-8')
                }, status=500)
                
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
@method_decorator(csrf_exempt, name='dispatch')
class DeepSpeechView(View):

    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)

        uploaded_file = request.FILES['file']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(uploaded_file.name, uploaded_file)

        # Define Paths on Shared Volume
        input_path = f"/data/uploads/{filename}"
        
        # We create a specific folder for DeepSpeech results
        output_folder_name = f"{os.path.splitext(filename)[0]}_deepspeech"
        output_folder_path = f"/data/outputs/{output_folder_name}"
        os.makedirs(output_folder_path, exist_ok=True)
        
        # The script expects an output prefix
        output_prefix = f"{output_folder_path}/result"

        try:
            # Connect to the SPECIFIC container: worker_deepspeech
            container = client.containers.get('worker_deepspeech')
            
            # Command: python main.py -i <input> -o <output>
            cmd = f"python main.py -i {input_path} -o {output_prefix}"
            
            exec_result = container.exec_run(cmd)
            
            if exec_result.exit_code == 0:
                return JsonResponse({
                    "status": "success",
                    "tool": "deepspeech",
                    "message": "Successfully run Deepspeech",
                    "output_location": output_folder_path
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "error": "Invalid file format",
                    "logs": exec_result.output.decode('utf-8')
                }, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
@method_decorator(csrf_exempt, name='dispatch')
class ffmpeg2_view(View):
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)

        uploaded_file = request.FILES['file']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(uploaded_file.name, uploaded_file)

        # 1. Define Paths
        input_path = f"/data/uploads/{filename}"
        
        # Create a folder for the results
        output_folder_name = f"{os.path.splitext(filename)[0]}_ffmpeg2"
        output_folder_path = f"/data/outputs/{output_folder_name}"
        os.makedirs(output_folder_path, exist_ok=True)
        
        # The script uses this prefix to name the .wav, .mp4 and .tar.gz
        output_prefix = f"{output_folder_path}/result"

        try:
            # 2. Connect to worker_ffmpeg2
            container = client.containers.get('worker_ffmpeg2')
            
            # Command: python main.py -i <input> -o <output>
            cmd = f"python main.py -i {input_path} -o {output_prefix}"
            
            exec_result = container.exec_run(cmd)
            
            if exec_result.exit_code == 0:
                return JsonResponse({
                    "status": "success",
                    "tool": "ffmpeg-2",
                    "logs": exec_result.output.decode('utf-8'),
                    "output_location": output_folder_path
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "logs": exec_result.output.decode('utf-8')
                }, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

@method_decorator(csrf_exempt, name='dispatch')
class ffmpeg0_view(View):
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)

        uploaded_file = request.FILES['file']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(uploaded_file.name, uploaded_file)

        # Define Paths
        input_path = f"/data/uploads/{filename}"
        
        # Unique output folder
        output_folder_name = f"{os.path.splitext(filename)[0]}_ffmpeg0"
        output_folder_path = f"/data/outputs/{output_folder_name}"
        os.makedirs(output_folder_path, exist_ok=True)
        
        # The script uses this prefix to name the final tar.gz
        output_prefix = f"{output_folder_path}/result"

        try:
            # Connect to the new worker
            container = client.containers.get('worker_ffmpeg0')
            
            cmd = f"python main.py -i {input_path} -o {output_prefix}"
            
            exec_result = container.exec_run(cmd)
            
            if exec_result.exit_code == 0:
                full_file_path = f"{output_prefix}.tar.gz"
                return JsonResponse({
                    "status": "success",
                    "tool": "ffmpeg-0",
                    "message": "Successfully run ffmpeg0",
                    "output_location": full_file_path
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "error": "Tool execution failed",
                    "logs": exec_result.output.decode('utf-8')
                }, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
@method_decorator(csrf_exempt, name='dispatch')
class LibrosaView(View):
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)

        uploaded_file = request.FILES['file']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(uploaded_file.name, uploaded_file)

        # Define Paths
        input_path = f"/data/uploads/{filename}"
        
        # Unique output folder
        output_folder_name = f"{os.path.splitext(filename)[0]}_librosa"
        output_folder_path = f"/data/outputs/{output_folder_name}"
        os.makedirs(output_folder_path, exist_ok=True)
        
        # Output prefix
        output_prefix = f"{output_folder_path}/result"

        try:
            # Connect to worker_librosa
            container = client.containers.get('worker_librosa')
            
            cmd = f"python main.py -i {input_path} -o {output_prefix}"
            
            exec_result = container.exec_run(cmd)
            
            if exec_result.exit_code == 0:
                return JsonResponse({
                    "status": "success",
                    "tool": "librosa-splitter",
                    "logs": exec_result.output.decode('utf-8'),
                    "output_location": output_folder_path
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "error": "Librosa processing failed",
                    "logs": exec_result.output.decode('utf-8')
                }, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)