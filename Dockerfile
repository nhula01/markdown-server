FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home markdown
COPY --chown=markdown:markdown app.py .
COPY --chown=markdown:markdown content ./content
COPY --chown=markdown:markdown pdfs ./pdfs
USER markdown
ENV PDF_ROOT=/app/pdfs MD_ROOT=/app/content PORT=8000
EXPOSE 8000
CMD ["sh","-c","exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --access-logfile - --error-logfile - app:application"]
