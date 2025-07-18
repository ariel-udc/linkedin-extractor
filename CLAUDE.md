# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CLI tool project for LinkedIn data extraction. The tool will:
- Login to LinkedIn.com programmatically
- Extract contact information and other data from the logged-in profile's perspective
- Provide a command-line interface for data extraction operations

## Development Setup

This project is in the initial phase. No build system, dependencies, or code structure has been established yet.

## Architecture Notes

When implementing this project, consider:
- **Authentication**: LinkedIn login mechanism (likely requiring web scraping or API integration)
- **Data Extraction**: Contact information, profile data, and other accessible information
- **CLI Interface**: Command-line argument parsing and user interaction
- **Data Storage**: How extracted data will be stored and formatted
- **Rate Limiting**: Respecting LinkedIn's usage policies and implementing appropriate delays
- **Error Handling**: Robust handling of authentication failures and network issues

## Security Considerations

- Never commit LinkedIn credentials to the repository
- Implement secure credential storage (environment variables, config files with proper permissions)
- Follow LinkedIn's Terms of Service and API usage guidelines
- Consider implementing user consent mechanisms for data extraction

## Technology Stack

Technology choices will depend on implementation decisions but may include:
- Programming language (Python, Node.js, etc.)
- Web scraping libraries (Selenium, Puppeteer, etc.)
- CLI framework
- Data storage format (JSON, CSV, etc.)