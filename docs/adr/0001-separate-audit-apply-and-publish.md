# Separate audit, apply, and publish

Repository history repair must proceed through Audit, explicit approval, Apply in an isolated repository copy, validation, and separate approval before Publish. Although a single automatic rewrite would be faster, rewritten commit IDs and remote references are disruptive and difficult to recover once collaborators, forks, releases, or automation consume them.
