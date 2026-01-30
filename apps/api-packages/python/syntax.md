# Atlas AI Python API Syntax

## Core Syntax

### Simplest Usage (No Model Specified - Uses thor-1.1)
```python
import atlas_ai

atlas_ai.agent("Hello")
# Output: Hello! How can I help you today?
```

### Direct Model Calls
```python
import atlas_ai

atlas_ai.thor_1_1("Hello")
atlas_ai.thor_lite_1_1("Hello")
```

### Storing Response in Variable
```python
import atlas_ai

response = atlas_ai.call("Hello")
print(response)  # Manual print if needed
```
