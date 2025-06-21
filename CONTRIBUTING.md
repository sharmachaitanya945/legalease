# Contributing to LegalEase AI

Thank you for your interest in contributing to LegalEase AI! This document provides guidelines for contributing to the project.

## 🛠️ Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/legalease-ai.git
   cd legalease-ai
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Fill in your actual values
   ```

## 🔄 Development Workflow

1. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** and test thoroughly
3. **Commit your changes**:
   ```bash
   git commit -m "Add: descriptive commit message"
   ```
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Create a Pull Request** on GitHub

## 📝 Code Style Guidelines

- **Python**: Follow PEP 8 style guidelines
- **JavaScript**: Use modern ES6+ syntax
- **HTML/CSS**: Use semantic markup and consistent naming
- **Comments**: Write clear, descriptive comments
- **Functions**: Keep functions small and focused
- **Variables**: Use descriptive variable names

## 🧪 Testing

- Test all new features thoroughly
- Ensure existing functionality still works
- Test with different file formats and edge cases
- Verify environment variable handling

## 🔒 Security Guidelines

- **Never commit sensitive data** (API keys, passwords, etc.)
- **Use environment variables** for all configuration
- **Validate all user inputs** properly
- **Sanitize file uploads** before processing
- **Follow security best practices**

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] Environment variables are properly used

### PR Description Should Include
- **What**: Brief description of changes
- **Why**: Reason for the changes
- **How**: Technical approach used
- **Testing**: How you tested the changes

## 🚀 Feature Requests

When requesting new features:
1. **Check existing issues** first
2. **Provide clear use cases**
3. **Explain the problem** you're solving
4. **Suggest implementation** if possible

## 🐛 Bug Reports

When reporting bugs:
1. **Use a clear title**
2. **Describe expected vs actual behavior**
3. **Provide steps to reproduce**
4. **Include error messages/logs**
5. **Specify environment details**

## 📚 Documentation

- Update README.md for new features
- Add inline comments for complex logic
- Update API documentation
- Include example usage

## 🎯 Areas for Contribution

- **Bug fixes**: Address issues in the issue tracker
- **New features**: Enhance existing functionality
- **Documentation**: Improve setup guides and examples
- **Testing**: Add comprehensive test coverage
- **Performance**: Optimize search and upload speeds
- **UI/UX**: Improve user interface and experience
- **Security**: Enhance security measures

## ❓ Questions?

If you have questions about contributing:
- Check the [README.md](README.md) first
- Look through existing issues
- Create a new issue with the "question" label

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to LegalEase AI! 🎉
