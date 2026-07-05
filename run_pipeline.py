from pipeline.ingestor import start_pipeline

if __name__ == "__main__":
    try:
        start_pipeline()
    except KeyboardInterrupt:
        print("\nPipeline intercepted. Shutting down...")