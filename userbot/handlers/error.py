# idk why i added (saste nashe)


import traceback

def safe_handler(filename, sync_callback=None):
    """
    Decorator to safely run a handler function and catch exceptions.
    """
    def decorator(func):
        async def wrapper(event, *args, **kwargs):
            try:
                await func(event, *args, **kwargs)
            except Exception as e:
                # Log exception to console
                print(f"Exception in handler {filename}: {e}")
                traceback.print_exc()

                # Optionally, update handler state as error
                from shared.state import mark_error
                if filename:
                    mark_error(filename)

                # Optionally call sync callback to update JSON
                if sync_callback:
                    import asyncio
                    asyncio.create_task(sync_callback())

        return wrapper
    return decorator
