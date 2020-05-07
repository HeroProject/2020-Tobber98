package org.bitbucket.socialrobotics;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.util.Collections;
import java.util.Map;

import fi.iki.elonen.NanoHTTPD;
import fi.iki.elonen.NanoHTTPD.Response.Status;

// Based on https://github.com/NanoHttpd/nanohttpd/blob/master/webserver/src/main/java/org/nanohttpd/webserver/SimpleWebServer.java
public class WebHttpServer extends NanoHTTPD {
	private final static String cors = "*";
	private final static String indexFile = "index.html";
	private final File homeDir;

	public WebHttpServer(final int port) throws Exception {
		super(port);
		this.homeDir = new File("html");
	}

	@Override
	public Response serve(final IHTTPSession session) {
		final Map<String, String> header = session.getHeaders();
		final String uri = session.getUri();

		System.out.println(session.getMethod() + " '" + uri + "' ");

		return respond(Collections.unmodifiableMap(header), session, uri);
	}

	private Response respond(final Map<String, String> headers, final IHTTPSession session, final String uri) {
		Response r;
		if (Method.OPTIONS.equals(session.getMethod())) {
			r = newFixedLengthResponse(Status.OK, MIME_PLAINTEXT, null, 0);
		} else {
			r = defaultResponse(headers, session, uri);
		}

		addCORSHeaders(headers, r, cors);

		return r;
	}

	private Response defaultResponse(final Map<String, String> headers, final IHTTPSession session, String uri) {
		uri = uri.trim().replace(File.separatorChar, '/');
		if (uri.indexOf('?') >= 0) {
			uri = uri.substring(0, uri.indexOf('?'));
		}

		if (uri.contains("../")) {
			return getForbiddenResponse("Won't serve ../ for security reasons");
		} else if (!canServeUri(uri, this.homeDir)) {
			return getNotFoundResponse();
		} else {
			final File f = new File(this.homeDir, uri);
			if (f.isDirectory()) {
				return respond(headers, session, uri + indexFile);
			} else {
				final String mimeTypeForFile = getMimeTypeForFile(uri);
				try {
					return newFixedFileResponse(f, mimeTypeForFile);
				} catch (final FileNotFoundException e) {
					return getNotFoundResponse();
				}
			}
		}
	}

	/*
	 * Helper functions
	 */

	private static boolean canServeUri(final String uri, final File homeDir) {
		final File f = new File(homeDir, uri);
		return f.exists();
	}

	private static Response getForbiddenResponse(final String s) {
		return newFixedLengthResponse(Status.FORBIDDEN, NanoHTTPD.MIME_PLAINTEXT, "FORBIDDEN: " + s);
	}

	/*private static Response getInternalErrorResponse(final String s) {
		return newFixedLengthResponse(Status.INTERNAL_ERROR, NanoHTTPD.MIME_PLAINTEXT, "INTERNAL ERROR: " + s);
	}*/

	private static Response getNotFoundResponse() {
		return newFixedLengthResponse(Status.NOT_FOUND, NanoHTTPD.MIME_PLAINTEXT, "Error 404, file not found.");
	}

	private static Response newFixedFileResponse(final File file, final String mime) throws FileNotFoundException {
		return NanoHTTPD.newFixedLengthResponse(Status.OK, mime, new FileInputStream(file), (int) file.length());
	}

	private static void addCORSHeaders(final Map<String, String> headers, final Response resp, final String cors) {
		resp.addHeader("Access-Control-Allow-Origin", cors);
		resp.addHeader("Access-Control-Allow-Headers", ALLOWED_HEADERS);
		resp.addHeader("Access-Control-Allow-Methods", ALLOWED_METHODS);
	}

	// defaults
	private final static String ALLOWED_METHODS = "GET, POST, PUT, DELETE, OPTIONS, HEAD";
	private final static String ALLOWED_HEADERS = "origin,accept,content-type";
}
