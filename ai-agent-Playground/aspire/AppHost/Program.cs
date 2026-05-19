var builder = DistributedApplication.CreateBuilder(args);

var servicemodelr = builder.AddDockerfile("servicemodelr", "../../servicemodelr")
    .WithHttpEndpoint(port: 8001, targetPort: 8000, name: "http")
    .WithOtlpExporter();

var addressvalidation = builder.AddDockerfile("addressvalidation", "../../addressvalidation")
    .WithHttpEndpoint(port: 8002, targetPort: 8000, name: "http")
    .WithOtlpExporter();

builder.Build().Run();
