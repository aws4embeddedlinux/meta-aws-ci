/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 */
import { Construct, Stage, StageProps } from '@aws-cdk/core';
import {YoctoImageBuilderStack} from './stacks/yocto-image-builder-stack';
import {YoctoBaseImageBuilderStack} from './stacks/yocto-base-image-builder-stack';
import { PrerequisitesStack } from './prerequisites-stack';


export interface ImageBuilderApplicationStageProps extends StageProps {
    readonly stage: string;
}

// The ImageBuilder application defines all the logic that need to be deployed.
// If you have a matrix of platforms and boards that need to be supported, you can loop or instanciate more
// of the builder stacks here, and they will get created for every environment you specified in the pipeline stack.
export class ImageBuilderApplication extends Stage {
    constructor(scope: Construct, id: string, props: ImageBuilderApplicationStageProps) {
        super(scope, id, props);

        const prerequisites = new PrerequisitesStack(this, 'PrerequisitesStack', {
            stage: props.stage
        });

        const baseImage = new YoctoBaseImageBuilderStack(this, 'YoctoBaseImageBuilderStack', {
            stage: props.stage,
            
            dockerSecretName: PrerequisitesStack.DockerSecretName,
            githubSecretName: PrerequisitesStack.GithubSecretName,

            githubBaseImageRepositoryBranch: PrerequisitesStack.GithubBaseImageRepositoryBranch,
            githubBaseImageRepositoryName: PrerequisitesStack.GithubBaseImageRepositoryName,
            githubBaseImageRepositoryOwner: PrerequisitesStack.GithubBaseImageRepositoryOwner,
            githubBaseImageRepositorySpecLocation: PrerequisitesStack.GithubBaseImageRepositorySpecLocation,
        });

        new YoctoImageBuilderStack(this, 'YoctoRaspberryPiImageBuilderStack', {
            vpc: prerequisites.Vpc, 
            stage: props.stage,
            
            baseImageRepository: baseImage.baseImageRepository,
            imageTag: baseImage.imageTag,

            githubSecretName: PrerequisitesStack.GithubSecretName,
            githubYoctoRecipeRepositoryName: PrerequisitesStack.GithubYoctoRecipeRepositoryName,
            githubYoctoRecipeRepositoryOwner: PrerequisitesStack.GithubYoctoRecipeRepositoryOwner,
            githubYoctoRecipeRepositoryBranch: PrerequisitesStack.GithubYoctoRecipeRepositoryBranch,
        });
    }
}