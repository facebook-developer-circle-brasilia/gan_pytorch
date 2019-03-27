import torch.nn as nn
import torch.optim as optim
import torch
import torchvision.datasets as dset
import torchvision.transforms as transforms
import os
import sys
import argparse

class Discriminator(nn.Module):
    
    def __init__(self, ngpu, nc, ndf):
        super(Discriminator, self).__init__()
        self.ngpu = ngpu
        self.main = nn.Sequential(
            # input is (nc) x 64 x 64
            nn.Conv2d(nc, ndf, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf) x 32 x 32
            nn.Conv2d(ndf, ndf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf*2) x 16 x 16
            nn.Conv2d(ndf * 2, ndf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf*4) x 8 x 8
            nn.Conv2d(ndf * 4, ndf * 8, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf*8) x 4 x 4
            nn.Conv2d(ndf * 8, 1, 4, 1, 0, bias=False),
            nn.Sigmoid()
        )

    def forward(input_data):
        return self.main(input_data)

class Generator(nn.Module):

    def __init__(self, ngpu, nz, nc, ngf):
        super(Generator, self).__init__()
        self.ngpu = ngpu
        self.main = nn.Sequential(
            # input is Z, going into a convolution
            nn.ConvTranspose2d( nz, ngf * 8, 4, 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 8),
            nn.ReLU(True),
            # state size. (ngf*8) x 4 x 4
            nn.ConvTranspose2d(ngf * 8, ngf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 4),
            nn.ReLU(True),
            # state size. (ngf*4) x 8 x 8
            nn.ConvTranspose2d( ngf * 4, ngf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 2),
            nn.ReLU(True),
            # state size. (ngf*2) x 16 x 16
            nn.ConvTranspose2d( ngf * 2, ngf, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf),
            nn.ReLU(True),
            # state size. (ngf) x 32 x 32
            nn.ConvTranspose2d( ngf, nc, 4, 2, 1, bias=False),
            nn.Tanh()
            # state size. (nc) x 64 x 64
        )

    def forward(input_data):
        return self.main(input_data)

def weights_init(m):
    # weights shall be randomly initialized from a Normal distribution with mean=0, stdev=0.2
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)

def main(args):

    print("Initializing Dataset...")
    # We can use an image folder dataset the way we have it setup.
    # Create the dataset
    dataset = dset.ImageFolder(root=args.dataset_path,
                            transform=transforms.Compose([
                                transforms.Resize(args.image_size),
                                transforms.CenterCrop(args.image_size),
                                transforms.ToTensor(),
                                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                            ]))
    # Create the dataloader
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
                                            shuffle=True, num_workers=workers)

    print(dataloader)

    device = torch.device("cuda:0" if (torch.cuda.is_available() and args.ngpu > 0) else "cpu")

    print("Creating Generator...")
    gen = Generator(args.ngpu, args.nz, args.nc, args.ngf).to(device)

    gen.apply(weights_init)

    print(gen, '\n')

    print("Creating Discriminator...")
    dis = Discriminator(args.ngpu, args.nc, args.ndf).to(device)
    dis.apply(weights_init)

    print(dis, '\n')

    print("Setting up loss and optimizer...\n")
    
    loss = nn.BCELoss()
    
    optimizer_d = optim.Adam(dis.parameters(), lr=args.learning_rate, betas=(0.5, 0.999))
    optimizer_g = optim.Adam(gen.parameters(), lr=args.learning_rate, betas=(0.5, 0.999))
    
    real_label = 1
    fake_label = 0

    # print("Starting DCGAN train...")
    # for epoch in range(args.epochs):
        # for i, data in enumerate(dataloader, 0):

        #     ############################
        #     # (1) Update D network: maximize log(D(x)) + log(1 - D(G(z)))
        #     ###########################
        #     ## Train with all-real batch
        #     netD.zero_grad()
        #     # Format batch
        #     real_cpu = data[0].to(device)
        #     b_size = real_cpu.size(0)
        #     label = torch.full((b_size,), real_label, device=device)
        #     # Forward pass real batch through D
        #     output = netD(real_cpu).view(-1)
        #     # Calculate loss on all-real batch
        #     errD_real = criterion(output, label)
        #     # Calculate gradients for D in backward pass
        #     errD_real.backward()
        #     D_x = output.mean().item()

        #     ## Train with all-fake batch
        #     # Generate batch of latent vectors
        #     noise = torch.randn(b_size, nz, 1, 1, device=device)
        #     # Generate fake image batch with G
        #     fake = netG(noise)
        #     label.fill_(fake_label)
        #     # Classify all fake batch with D
        #     output = netD(fake.detach()).view(-1)
        #     # Calculate D's loss on the all-fake batch
        #     errD_fake = criterion(output, label)
        #     # Calculate the gradients for this batch
        #     errD_fake.backward()
        #     D_G_z1 = output.mean().item()
        #     # Add the gradients from the all-real and all-fake batches
        #     errD = errD_real + errD_fake
        #     # Update D
        #     optimizerD.step()

        #     ############################
        #     # (2) Update G network: maximize log(D(G(z)))
        #     ###########################
        #     netG.zero_grad()
        #     label.fill_(real_label)  # fake labels are real for generator cost
        #     # Since we just updated D, perform another forward pass of all-fake batch through D
        #     output = netD(fake).view(-1)
        #     # Calculate G's loss based on this output
        #     errG = criterion(output, label)
        #     # Calculate gradients for G
        #     errG.backward()
        #     D_G_z2 = output.mean().item()
        #     # Update G
        #     optimizerG.step()

        #     # Output training stats
        #     if i % 50 == 0:
        #         print('[%d/%d][%d/%d]\tLoss_D: %.4f\tLoss_G: %.4f\tD(x): %.4f\tD(G(z)): %.4f / %.4f'
        #             % (epoch, num_epochs, i, len(dataloader),
        #                 errD.item(), errG.item(), D_x, D_G_z1, D_G_z2))

        #     # Save Losses for plotting later
        #     G_losses.append(errG.item())
        #     D_losses.append(errD.item())

        #     # Check how the generator is doing by saving G's output on fixed_noise
        #     if (iters % 500 == 0) or ((epoch == num_epochs-1) and (i == len(dataloader)-1)):
        #         with torch.no_grad():
        #             fake = netG(fixed_noise).detach().cpu()
        #         img_list.append(vutils.make_grid(fake, padding=2, normalize=True))

        #     iters += 1


def parse_arguments(argv):
    
    parser = argparse.ArgumentParser()

    parser.add_argument('--ngpu', type=int, default=1)
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--image_size', type=int, default=64)
    parser.add_argument('--learning_rate', type=int, default=0.0002)
    parser.add_argument('--nc', type=int, default=3)
    parser.add_argument('--nz', type=int, default=100)
    parser.add_argument('--ndf', type=int, default=64)
    parser.add_argument('--ngf', type=int, default=64)
    parser.add_argument('--dataset_path', type=str, default='dataset/img_align_celeba')
    parser.add_argument('--path2save', type=str, default=os.getcwd())

    return parser.parse_args(argv)

if __name__ == "__main__":
    main(parse_arguments(sys.argv[1:]))