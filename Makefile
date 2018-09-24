all: build open clean tarr
.PHONY: all clean tarr

latex_summary_input := summary.tex
latex_summary_output := summary.pdf

latex_summary_pdfa := summary.pdfa

latex_input := thesis.tex
latex_output := thesis.pdf

latex ?= pdflatex
bibtex ?= bibtex
gs ?= gs

# img_directory = img
pre_directory := 00-pre
mooncloud_directory := 01-mooncloud
vpn_directory := 02-vpn
ovpn_directory := 03-ovpnconf
nftables_directory := 04-nftables
security_directory := 05-security
microservice_directory := 06-microservice
img_directory := img
code_samples_directory := code_samples

#  pre_files := $(pre_directory)/index.tex
pre_files := $(pre_directory)/01_ack.tex
pre_files += $(pre_directory)/02_intro.tex

mooncloud_files := $(mooncloud_directory)/index.tex
mooncloud_files += $(mooncloud_directory)/01_overview.tex
mooncloud_files += $(mooncloud_directory)/02_archi.tex
mooncloud_files += $(mooncloud_directory)/03_not_only_cloud.tex

vpn_files := $(vpn_directory)/index.tex
vpn_files += $(vpn_directory)/00_intro.tex
vpn_files += $(vpn_directory)/01_openvpn.tex
vpn_files += $(vpn_directory)/02_softether.tex
vpn_files += $(vpn_directory)/03_ipsec.tex
vpn_files += $(vpn_directory)/04_others.tex
vpn_files += $(vpn_directory)/05_conclusions.tex

ovpn_files := $(ovpn_directory)/index.tex
ovpn_files += $(ovpn_directory)/01_softether.tex
ovpn_files += $(ovpn_directory)/02_ovpn_intro.tex
ovpn_files += $(ovpn_directory)/03_problems.tex
ovpn_files += $(ovpn_directory)/04_ip_mapping.tex
ovpn_files += $(ovpn_directory)/05_recap.tex
ovpn_files += $(ovpn_directory)/06_ending.tex
ovpn_files += $(ovpn_directory)/07_test.tex

nftables_files := $(nftables_directory)/index.tex
nftables_files += $(nftables_directory)/01_intro.tex
nftables_files += $(nftables_directory)/02_critics.tex
nftables_files += $(nftables_directory)/03_nftables.tex
nftables_files += $(nftables_directory)/04_how_used.tex

security_files := $(security_directory)/index.tex
security_files += $(security_directory)/01_openvpn_proto.tex
security_files += $(security_directory)/02_openvpn_conf.tex
security_files += $(security_directory)/03_openvpn_unused.tex
security_files += $(security_directory)/04_firewall_rules.tex
security_files += $(security_directory)/05_attacks.tex

microservice_files := $(microservice_directory)/index.tex
microservice_files += $(microservice_directory)/01_req.tex
microservice_files += $(microservice_directory)/02_archi.tex
microservice_files += $(microservice_directory)/03_details.tex
microservice_files += $(microservice_directory)/04_api.tex

code_files += $(code_samples_directory)/openssl.py
code_files += $(code_samples_directory)/nftables.py
code_files += $(code_samples_directory)/controllers_create_server.py
code_files += $(code_samples_directory)/controllers_create_client.py
code_files += $(code_samples_directory)/sshworker_loops.py
code_files += $(code_samples_directory)/works.lua

bib_file = bibliography.bib
bib_file_input = thesis

files := $(pre_files)
files += $(mooncloud_files)
files += $(vpn_files)
files += $(ovpn_files)
files += $(nftables_files)
files += $(security_files)
files += $(microservice_files)
files += $(bib_file)
files += $(code_files)
files += thesis.tex # thesis.pdf
files += $(bib_file)
# need to exclude thesis.pdf because it is a circular dependency,
# $(deps) is used as a dependency for thesis.pdf

img_files := $(img_directory)/minerva_2013_DI.jpg

img_files += $(img_directory)/mooncloud_archi.pdf
img_files += $(img_directory)/mooncloud_archi_extended.pdf

img_files += $(img_directory)/tunnelling.pdf

# img_files += $(img_directory)/mls.png
img_files += $(img_directory)/openvpn_sec.png
# img_files += $(img_directory)/rsmc.png
# img_files += $(img_directory)/rssc.png
# img_files += $(img_directory)/securenat.png
img_files += $(img_directory)/sls.png
img_files += $(img_directory)/softether_code_archi.jpg
img_files += $(img_directory)/softether_l2_lan_to_lan.png
img_files += $(img_directory)/softether_l3_lan_to_lan.png
img_files += $(img_directory)/softether_perf.jpg
img_files += $(img_directory)/softether_ras.jpg
img_files += $(img_directory)/softether_scheme_2.jpg
img_files += $(img_directory)/softether_scheme.jpg
img_files += $(img_directory)/wireguard_performance.png
img_files += $(img_directory)/NetfilterHooks.png
img_files += $(img_directory)/NetfilterIngress.png

img_files += $(img_directory)/ls.pdf
img_files += $(img_directory)/rsmc.pdf
img_files += $(img_directory)/rssc.pdf

img_files += $(img_directory)/openvpn_tunnelling.pdf

img_files += $(img_directory)/ip_mapping_send.pdf
img_files += $(img_directory)/ip_mapping_recv.pdf

img_files += $(img_directory)/openvpn_test1.pdf
img_files += $(img_directory)/openvpn_test2.pdf

img_files += $(img_directory)/microservice_deployment.pdf
img_files += $(img_directory)/activity_generic_file_transfer.pdf
img_files += $(img_directory)/sequence_mapping.pdf

summary_files := $(latex_summary_input)

# aux_files := *.aux

# deps := $(files)
all_deps := $(files) $(img_files)

tar_deps := $(all_deps)
tar_deps += $(summary_files)

tar_dest  := /media/nicola/Drive/BackupTar/thesis3.tar.bz2
gdrive_dest_dir := /home/nicola/GDrive
gdrive_dest_file := /home/nicola/GDrive/backs-tar/thesis3.tar.bz2

tar_exclude := .git

$(latex_output): $(all_deps) Makefile
	$(latex) -file-line-error --shell-escape $(latex_input)
	$(bibtex) $(bib_file_input)
	$(latex) -file-line-error --shell-escape $(latex_input)
	$(latex) -file-line-error --shell-escape $(latex_input)

$(latex_summary_output): $(summary_files)
	$(latex) -file-line-error $(latex_summary_input)
	$(latex) -file-line-error $(latex_summary_input)

$(latex_summary_pdfa): $(latex_summary_output)
	$(gs) -dCompatibilityLevel=1.4 \
			-dPDFA -dBATCH -dNOPAUSE \
			-dNOOUTERSAVE -sPDFACompatibilityPolicy=2 \
			-sProcessColorModel=DeviceCMYK \
			-sDEVICE=pdfwrite \
			-sOutputFile=$(latex_summary_pdfa) \
			$(latex_summary_output)


$(tar_dest): $(tar_deps)
	tar --exclude=$(tar_exclude) -cjf $(tar_dest) $(PWD)
	test -d $(gdrive_dest_dir) && cp $(tar_dest) $(gdrive_dest_file)
	test -d $(gdrive_dest_dir) && ls -l $(gdrive_dest_file)

build: $(latex_output)

summary: $(latex_summary_output) open-summary clean tarr

open:
	gvfs-open $(latex_output) 2> /dev/null &

open-summary:
	gvfs-open $(latex_summary_output) 2> /dev/null &

tarr: $(tar_dest)

clean:
	rm -f *.aux
	rm -f *.log
	rm -f *.toc
	rm -f *.out
	rm -f *.nav
	rm -f *.idx
	rm -f *.pyg
	rm -f *.bbl
	rm -f *.blg
	rm -f *.lof
