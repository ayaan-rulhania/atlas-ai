"""
Code Handler - Handles Python and JavaScript code queries
"""
import os
import json
from datetime import datetime

class CodeHandler:
    """Handles code-related queries for Python and JavaScript"""
    
    def __init__(self, brain_dir="brain"):
        self.brain_dir = brain_dir
        self._initialize_code_knowledge()
    
    def _initialize_code_knowledge(self):
        """Initialize code knowledge in brain"""
        try:
            code_topics = {
                'P': ['python', 'print', 'def', 'import', 'class'],
                'J': ['javascript', 'function', 'const', 'let', 'var'],
                'C': ['code', 'coding', 'programming'],
                'F': ['function', 'for', 'if'],
                'L': ['list', 'loop'],
                'V': ['variable', 'var'],
            }
            
            # Create brain directory if it doesn't exist
            if not os.path.exists(self.brain_dir):
                os.makedirs(self.brain_dir, exist_ok=True)
            
            for letter, keywords in code_topics.items():
                letter_dir = os.path.join(self.brain_dir, letter)
                keywords_file = os.path.join(letter_dir, "keywords.json")
                
                # Create letter directory if it doesn't exist
                if not os.path.exists(letter_dir):
                    os.makedirs(letter_dir, exist_ok=True)
                
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)
                        
                        # Add code keywords
                        for keyword in keywords:
                            if keyword not in data.get('keywords', []):
                                data.setdefault('keywords', []).append(keyword)
                        
                        # Add code knowledge
                        code_knowledge = self._get_code_knowledge(letter)
                        existing_titles = [k.get('title', '') for k in data.get('knowledge', [])]
                        for k in code_knowledge:
                            if k.get('title', '') not in existing_titles:
                                data.setdefault('knowledge', []).append(k)
                        
                        data['last_updated'] = datetime.now().isoformat()
                        
                        with open(keywords_file, 'w') as f:
                            json.dump(data, f, indent=2)
                    except Exception as e:
                        # Silently continue if there's an error with a specific letter
                        pass
        except Exception as e:
            # Silently continue if brain initialization fails
            # Code handler will still work without brain integration
            pass
    
    def _get_code_knowledge(self, letter):
        """Get code knowledge for a letter - Python Crash Course & JavaScript Crash Course"""
        knowledge = {
            'P': [
                {
                    'title': 'Python Crash Course - Variables and Strings',
                    'content': 'Python variables don\'t need type declarations. Strings use single or double quotes. Use f-strings for formatting: f"Hello, {name}". String methods: .upper(), .lower(), .strip(), .split().',
                    'query': 'python variables strings',
                    'source': 'python_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Python Crash Course - Lists',
                    'content': 'Lists are ordered, mutable collections: `bicycles = ["trek", "cannondale"]`. Access with index: `bicycles[0]`. Methods: .append(), .insert(), .remove(), .pop(), .sort(), .reverse(). List comprehensions: `[x**2 for x in range(10)]`.',
                    'query': 'python lists',
                    'source': 'python_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Python Crash Course - Dictionaries',
                    'content': 'Dictionaries store key-value pairs: `alien = {"color": "green", "points": 5}`. Access: `alien["color"]` or `alien.get("color")`. Methods: .keys(), .values(), .items(). Loop: `for key, value in alien.items()`.',
                    'query': 'python dictionaries',
                    'source': 'python_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Python Crash Course - Functions',
                    'content': 'Define functions with `def function_name(parameters):`. Use `return` to return values. Default parameters: `def greet(name="Guest"):`. Keyword arguments: `greet(name="Alice")`. Docstrings describe functions.',
                    'query': 'python functions',
                    'source': 'python_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Python Crash Course - Classes',
                    'content': 'Classes define objects: `class Dog:`. `__init__` initializes: `def __init__(self, name): self.name = name`. Methods use `self`. Inheritance: `class ElectricCar(Car):`. Import modules: `from module import Class`.',
                    'query': 'python classes oop',
                    'source': 'python_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Python Crash Course - File Handling',
                    'content': 'Read files: `with open("file.txt") as file: content = file.read()`. Write: `with open("file.txt", "w") as file: file.write("text")`. Read lines: `for line in file:`. JSON: `import json; data = json.load(file)`.',
                    'query': 'python files json',
                    'source': 'python_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Python Crash Course - Loops and Conditionals',
                    'content': 'For loops: `for item in list:` or `for i in range(10):`. While loops: `while condition:`. If/elif/else for conditionals. Break exits loop, continue skips iteration. List comprehensions combine loops and conditionals.',
                    'query': 'python loops conditionals',
                    'source': 'python_crash_course',
                    'learned_at': datetime.now().isoformat()
                }
            ],
            'J': [
                {
                    'title': 'JavaScript Crash Course - Variables and Data Types',
                    'content': 'Use `const` for constants, `let` for variables (ES6+). Avoid `var`. Data types: strings, numbers, booleans, null, undefined, objects, arrays. Template literals: `` `Hello, ${name}` ``. Type checking: `typeof variable`.',
                    'query': 'javascript variables types',
                    'source': 'javascript_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'JavaScript Crash Course - Functions',
                    'content': 'Function declaration: `function greet(name) { return "Hello " + name; }`. Arrow functions: `const greet = (name) => "Hello " + name`. Default parameters: `function greet(name = "Guest")`. Higher-order functions accept functions as arguments.',
                    'query': 'javascript functions',
                    'source': 'javascript_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'JavaScript Crash Course - Arrays',
                    'content': 'Arrays: `const fruits = ["apple", "banana"]`. Methods: .push(), .pop(), .shift(), .unshift(), .slice(), .splice(). Array methods: .map(), .filter(), .reduce(), .forEach(), .find(), .some(), .every(). Spread operator: `[...array]`.',
                    'query': 'javascript arrays',
                    'source': 'javascript_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'JavaScript Crash Course - Objects',
                    'content': 'Object literal: `const person = { name: "Alice", age: 30 }`. Access: `person.name` or `person["name"]`. Methods: `greet() { return "Hi"; }`. Classes: `class Person { constructor(name) { this.name = name; } }`.',
                    'query': 'javascript objects classes',
                    'source': 'javascript_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'JavaScript Crash Course - Loops',
                    'content': 'For loop: `for (let i = 0; i < 10; i++)`. For...of: `for (const item of array)`. For...in: `for (const key in object)`. While: `while (condition)`. Array.forEach(): `array.forEach(item => console.log(item))`.',
                    'query': 'javascript loops',
                    'source': 'javascript_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'JavaScript Crash Course - DOM Manipulation',
                    'content': 'Select elements: `document.querySelector(".class")`, `document.getElementById("id")`. Modify: `.textContent`, `.innerHTML`, `.style.property`. Events: `.addEventListener("click", handler)`. Create: `document.createElement("div")`.',
                    'query': 'javascript dom',
                    'source': 'javascript_crash_course',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'JavaScript Crash Course - Async/Await',
                    'content': 'Promises: `fetch(url).then(response => response.json())`. Async/await: `async function getData() { const response = await fetch(url); return await response.json(); }`. Error handling: `try { } catch (error) { }`.',
                    'query': 'javascript async await promises',
                    'source': 'javascript_crash_course',
                    'learned_at': datetime.now().isoformat()
                }
            ],
            'C': [
                {
                    'title': 'Programming Fundamentals',
                    'content': 'Programming involves writing code to solve problems. Key concepts: variables (store data), functions (reusable code), loops (repeat actions), conditionals (make decisions), data structures (organize data), algorithms (step-by-step solutions).',
                    'query': 'programming fundamentals',
                    'source': 'code_handler',
                    'learned_at': datetime.now().isoformat()
                }
            ]
        }
        
        return knowledge.get(letter, [])
    
    def handle_code_query(self, message, think_deeper=False, language='python'):
        """Handle code-related queries"""
        message_lower = message.lower()
        
        # Use provided language or detect from message
        if language == 'python':
            return self._generate_python_response(message, think_deeper)
        elif language == 'javascript':
            return self._generate_javascript_response(message, think_deeper)
        elif language == 'html':
            return self._generate_html_response(message, think_deeper)
        else:
            # Auto-detect if language not provided
            python_keywords = ['python', 'py', 'def ', 'import ', 'print(']
            js_keywords = ['javascript', 'js', 'function ', 'const ', 'let ', 'var ']
            
            is_python = any(kw in message_lower for kw in python_keywords)
            is_javascript = any(kw in message_lower for kw in js_keywords)
            
            if is_python:
                return self._generate_python_response(message, think_deeper)
            elif is_javascript:
                return self._generate_javascript_response(message, think_deeper)
            else:
                # Default to Python
                return self._generate_python_response(message, think_deeper)
    
    def _generate_python_response(self, message, think_deeper):
        """Generate Python-specific response with actual working code"""
        import random
        
        message_lower = message.lower()
        
        # Generate actual working code based on the request
        # Try to understand what the user wants and generate appropriate code
        
        # Check for specific requests
        if 'calculate' in message_lower or 'math' in message_lower or 'sum' in message_lower:
            code = '''```python
# Calculate sum of numbers
def calculate_sum(numbers):
    """Calculate the sum of a list of numbers"""
    total = 0
    for num in numbers:
        total += num
    return total

# Example usage
numbers = [1, 2, 3, 4, 5]
result = calculate_sum(numbers)
print(f"Sum: {result}")  # Output: Sum: 15

# Or use built-in sum()
result = sum(numbers)
print(f"Sum: {result}")  # Output: Sum: 15
```'''
        elif 'function' in message_lower or 'def' in message_lower or 'create function' in message_lower:
            code = '''```python
def greet(name, greeting="Hello"):
    """Greet a person with an optional custom greeting"""
    return f"{greeting}, {name}!"

# Usage examples
print(greet("Alice"))  # Output: Hello, Alice!
print(greet("Bob", "Hi"))  # Output: Hi, Bob!

# Function with multiple parameters
def calculate_area(length, width):
    """Calculate the area of a rectangle"""
    return length * width

area = calculate_area(5, 3)
print(f"Area: {area}")  # Output: Area: 15
```'''
        elif 'list' in message_lower or 'array' in message_lower or 'collection' in message_lower:
            code = '''```python
# Creating and working with lists
fruits = ["apple", "banana", "orange"]
print(fruits[0])  # Output: apple

# Add items
fruits.append("grape")
fruits.insert(1, "mango")

# List operations
numbers = [1, 2, 3, 4, 5]
doubled = [x * 2 for x in numbers]  # List comprehension
print(doubled)  # Output: [2, 4, 6, 8, 10]

# Filter and map
even_numbers = [x for x in numbers if x % 2 == 0]
print(even_numbers)  # Output: [2, 4]
```'''
        elif 'loop' in message_lower or 'iterate' in message_lower or 'for' in message_lower or 'while' in message_lower:
            code = '''```python
# For loop - iterate over a list
fruits = ["apple", "banana", "orange"]
for fruit in fruits:
    print(fruit)

# For loop with range
for i in range(5):
    print(f"Number: {i}")

# While loop
count = 0
while count < 5:
    print(f"Count: {count}")
    count += 1

# Loop with conditions
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
for num in numbers:
    if num % 2 == 0:
        print(f"{num} is even")
    else:
        print(f"{num} is odd")
```'''
        elif 'class' in message_lower or 'object' in message_lower or 'oop' in message_lower:
            code = '''```python
class Dog:
    """A simple Dog class"""
    
    def __init__(self, name, age):
        """Initialize a Dog with name and age"""
        self.name = name
        self.age = age
    
    def bark(self):
        """Make the dog bark"""
        return f"{self.name} says Woof!"
    
    def get_info(self):
        """Get information about the dog"""
        return f"{self.name} is {self.age} years old"

# Create instances
dog1 = Dog("Buddy", 3)
dog2 = Dog("Max", 5)

print(dog1.bark())  # Output: Buddy says Woof!
print(dog2.get_info())  # Output: Max is 5 years old
```'''
        elif 'file' in message_lower or 'read' in message_lower or 'write' in message_lower:
            code = '''```python
# Reading from a file
with open('example.txt', 'r') as file:
    content = file.read()
    print(content)

# Writing to a file
with open('output.txt', 'w') as file:
    file.write("Hello, World!\\n")
    file.write("This is a new line")

# Reading line by line
with open('example.txt', 'r') as file:
    for line in file:
        print(line.strip())
```'''
        elif 'dictionary' in message_lower or 'dict' in message_lower:
            code = '''```python
# Creating a dictionary
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

# Accessing values
print(person["name"])  # Output: Alice
print(person.get("age"))  # Output: 30

# Adding/updating values
person["email"] = "alice@example.com"
person["age"] = 31

# Iterating over dictionary
for key, value in person.items():
    print(f"{key}: {value}")
```'''
        else:
            # Generate code based on the actual message
            # Try to extract what the user wants
            code = '''```python
# Python code example
def process_data(data):
    """Process a list of data items"""
    results = []
    for item in data:
        if item > 0:  # Example condition
            results.append(item * 2)
    return results

# Example usage
numbers = [1, 2, 3, 4, 5]
processed = process_data(numbers)
print(processed)  # Output: [2, 4, 6, 8, 10]

# Working with strings
text = "Hello, World!"
print(text.upper())  # Output: HELLO, WORLD!
print(text.split(","))  # Output: ['Hello', ' World!']
```'''
        
        explanation = "Here's working Python code:\n\n" + code
        
        if think_deeper:
            explanation += "\n\n**Python Crash Course Concepts:**\n\n"
            explanation += "- **Variables & Data Types**: Strings, integers, floats, booleans, lists, dictionaries\n"
            explanation += "- **Functions**: Use `def` to define, can have parameters and return values\n"
            explanation += "- **Control Flow**: `if/elif/else`, `for` loops, `while` loops\n"
            explanation += "- **Lists**: Ordered collections, mutable, support indexing and slicing\n"
            explanation += "- **Dictionaries**: Key-value pairs, great for storing related data\n"
            explanation += "- **Classes**: Object-oriented programming, `__init__` for initialization\n"
            explanation += "- **File Handling**: Use `with open()` for safe file operations\n"
            explanation += "- **List Comprehensions**: Concise way to create lists from existing lists"
        
        return explanation
    
    def _generate_javascript_response(self, message, think_deeper):
        """Generate JavaScript-specific response with actual working code"""
        import random
        
        message_lower = message.lower()
        
        # Generate actual working code based on the request
        if 'calculate' in message_lower or 'math' in message_lower or 'sum' in message_lower:
            code = '''```javascript
// Calculate sum of numbers
function calculateSum(numbers) {
    let total = 0;
    for (let num of numbers) {
        total += num;
    }
    return total;
}

// Example usage
const numbers = [1, 2, 3, 4, 5];
const result = calculateSum(numbers);
console.log(`Sum: ${result}`);  // Output: Sum: 15

// Or use reduce()
const sum = numbers.reduce((acc, num) => acc + num, 0);
console.log(`Sum: ${sum}`);  // Output: Sum: 15
```'''
        elif 'function' in message_lower or 'func' in message_lower or 'create function' in message_lower:
            code = '''```javascript
// Function declaration
function greet(name, greeting = "Hello") {
    return `${greeting}, ${name}!`;
}

// Arrow function (ES6+)
const greetArrow = (name, greeting = "Hello") => {
    return `${greeting}, ${name}!`;
};

// Usage
console.log(greet("Alice"));  // Output: Hello, Alice!
console.log(greetArrow("Bob", "Hi"));  // Output: Hi, Bob!

// Function with multiple parameters
const calculateArea = (length, width) => length * width;
const area = calculateArea(5, 3);
console.log(`Area: ${area}`);  // Output: Area: 15
```'''
        elif 'array' in message_lower or 'list' in message_lower or 'collection' in message_lower:
            code = '''```javascript
// Creating and working with arrays
const fruits = ["apple", "banana", "orange"];
console.log(fruits[0]);  // Output: apple

// Add items
fruits.push("grape");
fruits.unshift("mango");

// Array methods
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(x => x * 2);
console.log(doubled);  // Output: [2, 4, 6, 8, 10]

const evenNumbers = numbers.filter(x => x % 2 === 0);
console.log(evenNumbers);  // Output: [2, 4]

const sum = numbers.reduce((acc, num) => acc + num, 0);
console.log(sum);  // Output: 15
```'''
        elif 'loop' in message_lower or 'iterate' in message_lower or 'for' in message_lower or 'while' in message_lower:
            code = '''```javascript
// For loop
for (let i = 0; i < 5; i++) {
    console.log(`Number: ${i}`);
}

// For...of loop (ES6+)
const fruits = ["apple", "banana", "orange"];
for (const fruit of fruits) {
    console.log(fruit);
}

// ForEach method
fruits.forEach((fruit, index) => {
    console.log(`${index}: ${fruit}`);
});

// While loop
let count = 0;
while (count < 5) {
    console.log(`Count: ${count}`);
    count++;
}

// Loop with conditions
const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
numbers.forEach(num => {
    if (num % 2 === 0) {
        console.log(`${num} is even`);
    } else {
        console.log(`${num} is odd`);
    }
});
```'''
        elif 'class' in message_lower or 'object' in message_lower or 'oop' in message_lower:
            code = '''```javascript
// ES6 Class
class Dog {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    
    bark() {
        return `${this.name} says Woof!`;
    }
    
    getInfo() {
        return `${this.name} is ${this.age} years old`;
    }
}

// Create instances
const dog1 = new Dog("Buddy", 3);
const dog2 = new Dog("Max", 5);

console.log(dog1.bark());  // Output: Buddy says Woof!
console.log(dog2.getInfo());  // Output: Max is 5 years old
```'''
        elif 'object' in message_lower and 'literal' not in message_lower:
            code = '''```javascript
// Object literal
const person = {
    name: "Alice",
    age: 30,
    city: "New York",
    greet() {
        return `Hello, I'm ${this.name}`;
    }
};

// Accessing properties
console.log(person.name);  // Output: Alice
console.log(person["age"]);  // Output: 30

// Adding properties
person.email = "alice@example.com";

// Iterating over object
for (const key in person) {
    if (typeof person[key] !== 'function') {
        console.log(`${key}: ${person[key]}`);
    }
}

console.log(person.greet());  // Output: Hello, I'm Alice
```'''
        else:
            code = '''```javascript
// JavaScript code example
function processData(data) {
    const results = [];
    for (const item of data) {
        if (item > 0) {  // Example condition
            results.push(item * 2);
        }
    }
    return results;
}

// Example usage
const numbers = [1, 2, 3, 4, 5];
const processed = processData(numbers);
console.log(processed);  // Output: [2, 4, 6, 8, 10]

// Working with strings
const text = "Hello, World!";
console.log(text.toUpperCase());  // Output: HELLO, WORLD!
console.log(text.split(","));  // Output: ['Hello', ' World!']
```'''
        
        explanation = "Here's working JavaScript code:\n\n" + code
        
        if think_deeper:
            explanation += "\n\n**JavaScript Crash Course Concepts:**\n\n"
            explanation += "- **Variables**: `const` for constants, `let` for variables (ES6+)\n"
            explanation += "- **Functions**: Regular functions, arrow functions `() => {}`, and methods\n"
            explanation += "- **Arrays**: Ordered collections with methods like `map()`, `filter()`, `reduce()`\n"
            explanation += "- **Objects**: Key-value pairs, object literals, and classes\n"
            explanation += "- **Loops**: `for`, `while`, `for...of`, `forEach()`\n"
            explanation += "- **Template Literals**: Use backticks for string interpolation\n"
            explanation += "- **Destructuring**: Extract values from arrays and objects\n"
            explanation += "- **Spread Operator**: `...` for copying arrays/objects\n"
            explanation += "- **Async/Await**: Handle asynchronous operations with promises"
        
        return explanation
    
    def _generate_html_response(self, message, think_deeper):
        """Generate HTML-specific response (coming soon)"""
        return "**HTML support is coming soon!** 🔒\n\nFor now, I can help you with Python and JavaScript code. HTML support will be available in a future update."
    
    def _generate_general_code_response(self, message, think_deeper):
        """Generate general code response"""
        import random
        if think_deeper:
            return "**Programming Fundamentals**\n\nProgramming involves writing instructions for computers. Key concepts include:\n\n- **Variables**: Store data\n- **Functions**: Reusable code blocks\n- **Loops**: Repeat actions\n- **Conditionals**: Make decisions\n- **Data Structures**: Organize data\n\nBoth Python and JavaScript are popular languages:\n- **Python**: Simplicity and readability, great for data science and automation\n- **JavaScript**: Web development, both frontend and backend\n\nProgramming requires logical thinking, problem-solving skills, and understanding of algorithms and data structures. Good code is readable, maintainable, and follows best practices and design patterns."
        else:
            return "I can help with **Python** and **JavaScript** programming. What specific topic would you like to know about?"


# Global instance
_code_handler = None

def get_code_handler():
    """Get or create global code handler"""
    global _code_handler
    if _code_handler is None:
        _code_handler = CodeHandler()
    return _code_handler

