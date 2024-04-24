"""Script for generating documentation."""


from cloudnetpy_qc.quality import Test

if __name__ == "__main__":
    print("| Test | Description |")
    print("| - | - |")
    for cls in sorted(Test.__subclasses__(), key=lambda cls: cls.__name__):
        print(f"| `{cls.__name__}` | {cls.description} |")
