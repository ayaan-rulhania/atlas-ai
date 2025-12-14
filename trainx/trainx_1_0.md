# TrainX 1.0: Domain-Specific Training Language

## About TrainX

TrainX 1.0 is a highly domain-specific programming language (DSL)
engineered for the purpose of mass, supervised training of your AI
model **Thor 1.0**.

Its primary function is to serve as a high-speed, scalable
data-generation layer that sits above your existing question-and-answer
entry platform. TrainX is designed to minimize repetition and leverage
patterns in your data, significantly accelerating the process of
creating thousands of unique, high-quality Q&A pairs for model
fine-tuning.

**Goal:** To make the creation of large, structured, supervised training
datasets faster and more scalable.\
**Method:** Utilizes pattern matching, variable substitution, and list
iteration to generate numerous Q&A pairs from a concise script.

------------------------------------------------------------------------

## Core Syntax and Patterns

TrainX syntax is structured around defining input patterns (questions)
and their associated canonical output patterns (answers).

------------------------------------------------------------------------

### 1. Simple Question-Answer Pair (Q:A)

This is the most direct syntax for defining a single, unique Q&A pair.

#### **Syntax**

-   `Q: [Question Text]` --- Defines the specific input query.\
-   `A: [Answer Text]` --- Defines the corresponding desired output.

#### **Example**

    Q: What is soccer?
    A: Soccer is a game played by two teams of eleven players with a round ball that may not be touched with the hands or arms during play except by the goalkeepers. The object of the game is to score goals by kicking or heading the ball into the opponents' goal.

------------------------------------------------------------------------

### 2. Alternative Question Phrasing (Q:A with Aliases)

This pattern allows a single canonical answer to be triggered by
multiple ways of phrasing the same question.

#### **Syntax**

Use the `/` character within the `Q` block to list alternative names or
phrasings that should map to the same conceptual answer.

> **Note:** The first item in the list is treated as the canonical
> entity name.

#### **Example**

    Q: Who is {"Babe Ruth" / "The Great Bambino" / "The Sultan of Swat"}?
    A: Babe Ruth was a legendary American baseball player, considered one of the greatest hitters in the history of the sport, known for his powerful home runs and iconic status.

This block generates **three** distinct Q&A pairs.

------------------------------------------------------------------------

### 3. Image Responses (Q (Image))

Use the `(Image)` qualifier on a `Q` block to generate image-specific
pairs. The compiler will:

- Canonicalize the question to a request such as `Create an image of ...`
  when you provide a short subject (e.g., `Q (Image): Thor` becomes
  `Q: Create an image of Thor`).
- Mark the pair with `type: image` for downstream UIs.
- Preserve the answer as the raw image URL. The Result Setter renders a
  preview (iframe + still image) for these pairs.

#### **Syntax**

```
Q (Image): <subject or question text>
A: <direct image URL>
```

#### **Examples**

```
Q (Image): Thor
A: https://upload.wikimedia.org/wikipedia/en/3/3c/Chris_Hemsworth_as_Thor.jpg

Q (Image): {"puppy" / "dog"}
A: https://images.pexels.com/photos/1805164/pexels-photo-1805164.jpeg
```

> Tip: You can still use aliases inside `(Image)` questions. Each alias
> produces its own image pair, all tagged as `type: image`.

------------------------------------------------------------------------

### 4. Repetitive/Iterative Question Generation (Lists and Substitution)

This is TrainX's core feature for achieving scalable training data
generation.

------------------------------------------------------------------------

#### **A. Defining a List**

Lists use key--value pairs (`"Key":"Value"`), where the Key is the
subject and the Value is the associated object.

#### **Syntax**

    List [VariableName] = ["Key1":"Value1", "Key2":"Value2", ...]

#### **Example**

    List countries = ["India":"New Delhi", "USA":"Washington D.C", "UK":"London"]

------------------------------------------------------------------------

#### **B. Generating Q&A Pairs with Iteration**

The list variable is referenced using curly braces. TrainX automatically
iterates through the list, generating a unique Q&A pair for each entry.

  -----------------------------------------------------------------------
  Substitution Marker       Substituted Value
  ------------------------- ---------------------------------------------
  `{countries}`             Key (e.g., `"India"`, `"USA"`)

  `{countries.object}`      Value (e.g., `"New Delhi"`,
                            `"Washington D.C"`)
  -----------------------------------------------------------------------

#### **Example**

    List countries = ["India":"New Delhi", "USA":"Washington D.C", "UK":"London"]

    Q: What is the capital of {countries}?
    A: The capital of {countries} is {countries.object}.

This expands into:

-   **Q:** What is the capital of India?\
    **A:** The capital of India is New Delhi.

-   **Q:** What is the capital of USA?\
    **A:** The capital of USA is Washington D.C.

-   **Q:** What is the capital of UK?\
    **A:** The capital of UK is London.
