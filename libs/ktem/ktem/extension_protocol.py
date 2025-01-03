import pluggy

hookspec = pluggy.HookspecMarker("ktem")
hookimpl = pluggy.HookimplMarker("ktem")


@hookspec
def ktem_declare_extensions() -> dict:  
    """Called before the run() function is executed.

    This hook is called without any arguments, and should return a dictionary.
    The dictionary has the following structure:

        ```
        {
            "id": str,      
            "name": str,  
            "version": str,
            "support_host": str,
            "functionality": {
                "reasoning": {
                    id: {                        
                        "name": str,
                        "callbacks": {},
                        "settings": {},
                    },
                },
                "index": {
                    "name": str,
                    "callbacks": {
                        "get_index_pipeline": callable,
                        "get_retrievers": {name: callable}
                    },
                    "settings": {},
                },
            },
        }
        ```
    """
