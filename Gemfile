# frozen_string_literal: true

source "https://rubygems.org"

# Pin zeitwerk to a version compatible with Ruby 3.1.x
gem "zeitwerk", "< 2.7.2"

gemspec

gem "html-proofer", "~> 5.0", group: :test

platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

gem "wdm", "~> 0.2.0", platforms: [:mingw, :x64_mingw, :mswin]

