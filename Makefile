all: build open clean tarr
.PHONY: all clean tarr

latex_input = thesis.tex
latex_output = thesis.pdf

latex ?= pdflatex

# img_directory = img
mooncloud_directory := 01-mooncloud
vpn_directory := 02-vpn
ovpn_directory := 03-ovpnconf
nftables_directory := 04-nftables
security_directory := 05-security
microservice_directory := 06-microservice
img_directory := img

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
ovpn_files += $(ovpn_directory)/04_ip_remapping.tex
ovpn_files += $(ovpn_directory)/05_recap.tex
ovpn_files += $(ovpn_directory)/06_ending.tex
ovpn_files += $(ovpn_directory)/07_test.tex

microservice_files := $(microservice_directory)/index.tex
microservice_files += $(microservice_directory)/01_req.tex

security_files := $(security_directory)/index.tex
security_files += $(security_directory)/01_openvpn_proto.tex
security_files += $(security_directory)/02_openvpn_conf.tex
security_files += $(security_directory)/03_openvpn_unused.tex
security_files += $(security_directory)/04_firewall_rules.tex

security_files += $(security_directory)/05_attacks.tex

nftables_files := $(nftables_directory)/index.tex
nftables_files += $(nftables_directory)/01_intro.tex
nftables_files += $(nftables_directory)/02_critics.tex
nftables_files += $(nftables_directory)/03_nftables.tex
nftables_files += $(nftables_directory)/04_how_used.tex

bib_file = bib.tex

files := $(mooncloud_files)
files += $(vpn_files)
files += $(ovpn_files)
files += $(nftables_files)
files += $(security_files)
files += $(microservice_files)
files += $(bib_file)
files += thesis.tex # thesis.pdf
# need to exclude thesis.pdf because it is a circular dependency,
# $(deps) is used as a dependency for thesis.pdf

img_files := $(img_directory)/minerva_2013_DI.jpg
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

aux_files := *.aux

deps := $(files)
all_deps := $(files) $(img_files)

tar_dest  := /media/nicola/Drive/BackupTar/thesis3.tar.bz2
gdrive_dest_dir := /home/nicola/GDrive
gdrive_dest_file := /home/nicola/GDrive/backs-tar/thesis3.tar.bz2

tar_exclude := .git

$(latex_output): $(deps)
	$(latex) -file-line-error --shell-escape $(latex_input)
	$(latex) -file-line-error --shell-escape $(latex_input)

$(tar_dest): $(all_deps)
	tar --exclude=$(tar_exclude) -cjf $(tar_dest) $(PWD)
	test -d $(gdrive_dest_dir) && cp $(tar_dest) $(gdrive_dest_file)
	test -d $(gdrive_dest_dir) && ls -l $(gdrive_dest_file)

build: $(latex_output)

open:
	gvfs-open $(latex_output) 2> /dev/null &

tarr: $(tar_dest)

clean:
	# rm -f *.aux
	rm -f $(aux_files)
	rm -f *.log
	rm -f *.toc
	rm -f *.out
	rm -f *.nav
	rm -f *.idx
	rm -rf _minted-thesis
	# rm -f *.snm
