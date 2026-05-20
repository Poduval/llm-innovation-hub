using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

// Optional: repo-root .env (ai-agent-playground/../.env) for LiteLLM provider keys
LoadEnvFile(Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../.env")));

var litellmMasterKey = Env("LITELLM_MASTER_KEY", "sk-litellm-local");
var pipelinesApiKey = Env("PIPELINES_API_KEY", "0p3n-w3bu!");

var servicemodelr = builder.AddDockerfile("servicemodelr", "../../servicemodelr")
    .WithHttpEndpoint(port: 8001, targetPort: 8000, name: "http")
    .WithOtlpExporter();

var addressvalidation = builder.AddDockerfile("addressvalidation", "../../addressvalidation")
    .WithHttpEndpoint(port: 8002, targetPort: 8000, name: "http")
    .WithOtlpExporter();

var litellm = builder.AddContainer("litellm", "docker.litellm.ai/berriai/litellm", "main-stable")
    .WithBindMount("../../litellm/config.yaml", "/app/config.yaml", isReadOnly: true)
    .WithArgs("--config", "/app/config.yaml", "--port", "4000")
    .WithHttpEndpoint(port: 4000, targetPort: 4000, name: "http")
    .WithEnvironment("LITELLM_MASTER_KEY", litellmMasterKey)
    .WithEnvironment("NVIDIA_API_KEY", Env("NVIDIA_API_KEY", ""))
    .WithEnvironment("GROQ_API_KEY", Env("GROQ_API_KEY", ""))
    .WithEnvironment("MISTRAL_API_KEY", Env("MISTRAL_API_KEY", ""))
    .WithOtlpExporter();

var pipelines = builder.AddContainer("pipelines", "ghcr.io/open-webui/pipelines", "main")
    .WithBindMount("../../agents", "/app/pipelines")
    .WithHttpEndpoint(port: 9099, targetPort: 9099, name: "http")
    .WithEnvironment("PIPELINES_API_KEY", pipelinesApiKey)
    .WaitFor(litellm)
    .WaitFor(servicemodelr)
    .WaitFor(addressvalidation)
    .WithOtlpExporter();

builder.AddContainer("open-webui", "ghcr.io/open-webui/open-webui", "main")
    .WithHttpEndpoint(port: 3000, targetPort: 8080, name: "http")
    .WithEnvironment("OPENAI_API_BASE_URLS", "http://litellm:4000/v1;http://pipelines:9099")
    .WithEnvironment("OPENAI_API_KEYS", $"{litellmMasterKey};{pipelinesApiKey}")
    .WithEnvironment("ENABLE_OLLAMA_API", "false")
    .WithEnvironment("WEBUI_SECRET_KEY", Env("WEBUI_SECRET_KEY", "change-me-in-production"))
    .WithVolume("open-webui-data", "/app/backend/data")
    .WaitFor(litellm)
    .WaitFor(pipelines)
    .WaitFor(servicemodelr)
    .WaitFor(addressvalidation);

builder.Build().Run();

static string Env(string key, string fallback) =>
    string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable(key))
        ? fallback
        : Environment.GetEnvironmentVariable(key)!;

static void LoadEnvFile(string path)
{
    if (!File.Exists(path))
        return;

    foreach (var raw in File.ReadAllLines(path))
    {
        var line = raw.Trim();
        if (line.Length == 0 || line.StartsWith('#'))
            continue;
        var i = line.IndexOf('=');
        if (i <= 0)
            continue;
        var key = line[..i].Trim();
        var value = line[(i + 1)..].Trim().Trim('"');
        if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable(key)))
            Environment.SetEnvironmentVariable(key, value);
    }
}
