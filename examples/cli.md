# Example: CLI (cli.cbl)

This example shows a minimal pattern for CLI utilities. Real projects should parse `argv` from C via externs or provide a small runtime helper.

Code (cli.cbl):

```cbl
func main() -> int {
    // Very simple CLI pattern (pseudo-args handling)
    print("CBlerr CLI example")
    return 0
}
```

Explanation:
- For real argument handling, declare `extern` C functions to access `main` arguments or extend the compiler to pass `argv` into `main`.
