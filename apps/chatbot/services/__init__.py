"""Local services shim.

The full Atlas runtime uses Thor's `thor-1.0/services` package.
For lightweight/serverless deployments (e.g., Vercel where we deploy only
`chatbot/`), this package provides the minimal modules needed by the
frontend/refinement stack.

Do not add heavy ML dependencies here.
"""
